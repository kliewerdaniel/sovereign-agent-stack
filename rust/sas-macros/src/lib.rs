//! Proc-macro crate for Sovereign Agent Stack.
//!
//! Provides `#[derive(Tool)]` and related macros for compile-time tool schema
//! generation, validation, and capability-bound execution.

use proc_macro::TokenStream;
use quote::quote;
use syn::{
    parse_macro_input, DeriveInput, Data, DataStruct, Fields, FieldsNamed,
    Attribute, LitStr, Expr, ExprLit, Lit, Meta, MetaNameValue, Type, Path,
    GenericArgument, PathArguments, AngleBracketedGenericArguments,
};

mod attrs;

/// Derive macro for the `Tool` trait.
///
/// Generates:
/// - `Tool::name()` — tool identifier (snake_case of struct name)
/// - `Tool::description()` — from `#[tool(description = "...")]` attribute
/// - `Tool::schema()` — JSON Schema for the tool's input parameters
/// - `Tool::validate()` — compile-time + runtime input validation
/// - `Tool::execute()` — dispatch to the tool's `run()` method
///
/// # Example
///
/// ```ignore
/// #[derive(Tool)]
/// #[tool(description = "Query the compile-time knowledge graph")]
/// struct QueryKnowledge {
///     query: String,
///     #[tool(default = "10")]
///     limit: u32,
/// }
/// ```
#[proc_macro_derive(Tool, attributes(tool))]
pub fn derive_tool(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);

    let name = &input.ident;
    let name_str = name.to_string();
    let snake_name = to_snake_case(&name_str);

    // Extract tool-level attributes
    let tool_attrs = ToolAttrs::from_attrs(&input.attrs);
    let description = tool_attrs.description.as_deref().unwrap_or("");

    // Extract fields
    let fields = match &input.data {
        Data::Struct(DataStruct {
            fields: Fields::Named(FieldsNamed { named, .. }),
            ..
        }) => named,
        _ => panic!("#[derive(Tool)] only supports structs with named fields"),
    };

    let field_infos: Vec<FieldInfo> = fields.iter().map(FieldInfo::from_field).collect();

    // Generate schema
    let schema_gen = generate_schema(&field_infos, description, &snake_name);

    // Generate validate method
    let validate_gen = generate_validate(&field_infos);

    // Generate execute method (calls `run`)
    let execute_gen = generate_execute(name, &field_infos);

    // Generate Tool trait implementation
    let expanded = quote! {
        impl sas_core_rs::Tool for #name {
            fn name() -> &'static str {
                #snake_name
            }

            fn description() -> &'static str {
                #description
            }

            fn schema() -> sas_core_rs::JsonSchema {
                #schema_gen
            }

            fn validate(input: &serde_json::Value) -> Result<(), sas_core_rs::ValidationError> {
                #validate_gen
            }

            fn execute(input: serde_json::Value) -> Result<serde_json::Value, sas_core_rs::ToolError> {
                #execute_gen
            }
        }
    };

    TokenStream::from(expanded)
}

/// Generate the JSON Schema for a tool's input.
fn generate_schema(fields: &[FieldInfo], description: &str, name: &str) -> proc_macro2::TokenStream {
    let required_fields: Vec<&FieldInfo> = fields.iter().filter(|f| f.required).collect();

    let required_array = if required_fields.is_empty() {
        quote! { None }
    } else {
        let names: Vec<&str> = required_fields.iter().map(|f| f.name.as_str()).collect();
        quote! { Some(vec![#(#names.to_string()),*]) }
    };

    let properties_entries: Vec<proc_macro2::TokenStream> = fields.iter().map(|f| {
        let name = &f.name;
        let ty_str = type_to_json_type(&f.ty);
        let desc = f.description.as_deref().unwrap_or("");
        let default_val = f.default.as_ref().map(|d| quote! { Some(serde_json::json!(#d)) }).unwrap_or_else(|| quote! { None });

        quote! {
            (
                #name.to_string(),
                sas_core_rs::SchemaProperty {
                    ty: #ty_str.to_string(),
                    description: if #desc.is_empty() { None } else { Some(#desc.to_string()) },
                    default: #default_val,
                },
            )
        }
    }).collect();

    quote! {
        sas_core_rs::JsonSchema {
            name: #name.to_string(),
            description: if #description.is_empty() { None } else { Some(#description.to_string()) },
            required: #required_array,
            properties: std::collections::HashMap::from([
                #(#properties_entries),*
            ]),
        }
    }
}

/// Generate the validate method body.
fn generate_validate(fields: &[FieldInfo]) -> proc_macro2::TokenStream {
    let validations: Vec<proc_macro2::TokenStream> = fields.iter().map(|f| {
        let name = &f.name;
        let ty_str = type_to_json_type(&f.ty);

        if f.required {
            quote! {
                {
                    let val = input.get(#name);
                    if val.is_none() {
                        return Err(sas_core_rs::ValidationError::MissingField(#name.to_string()));
                    }
                    if !sas_core_rs::validate_type(val.unwrap(), #ty_str) {
                        return Err(sas_core_rs::ValidationError::InvalidType {
                            field: #name.to_string(),
                            expected: #ty_str.to_string(),
                        });
                    }
                }
            }
        } else {
            quote! {
                {
                    if let Some(val) = input.get(#name) {
                        if !sas_core_rs::validate_type(val, #ty_str) {
                            return Err(sas_core_rs::ValidationError::InvalidType {
                                field: #name.to_string(),
                                expected: #ty_str.to_string(),
                            });
                        }
                    }
                }
            }
        }
    }).collect();

    quote! {
        #(#validations)*
        Ok(())
    }
}

/// Generate the execute method body.
fn generate_execute(name: &syn::Ident, fields: &[FieldInfo]) -> proc_macro2::TokenStream {
    let field_extracts: Vec<proc_macro2::TokenStream> = fields.iter().map(|f| {
        let name = &f.name;
        let ty = &f.ty;

        if f.required {
            quote! {
                let #name: #ty = serde_json::from_value(
                    input.get(#name).cloned().unwrap_or(serde_json::Value::Null)
                ).map_err(|e| sas_core_rs::ToolError::ParseError(e.to_string()))?;
            }
        } else {
            quote! {
                let #name: Option<#ty> = if let Some(v) = input.get(#name) {
                    Some(serde_json::from_value(v.clone()).map_err(|e| sas_core_rs::ToolError::ParseError(e.to_string()))?)
                } else {
                    None
                };
            }
        }
    }).collect();

    let field_names: Vec<&syn::Ident> = fields.iter().map(|f| {
        f.ident.as_ref().unwrap()
    }).collect();

    quote! {
        #(#field_extracts)*
        let instance = #name { #(#field_names),* };
        instance.run()
    }
}

// ── helpers ──────────────────────────────────────────────────────────────────

fn to_snake_case(s: &str) -> String {
    let mut result = String::new();
    for (i, ch) in s.chars().enumerate() {
        if ch.is_uppercase() {
            if i > 0 {
                result.push('_');
            }
            result.push(ch.to_lowercase().next().unwrap());
        } else {
            result.push(ch);
        }
    }
    result
}

fn type_to_json_type(ty: &Type) -> &'static str {
    if let Type::Path(type_path) = ty {
        if let Some(segment) = type_path.path.segments.last() {
            match segment.ident.to_string().as_str() {
                "String" => return "string",
                "u32" | "u64" | "i32" | "i64" | "usize" | "isize" => return "integer",
                "f32" | "f64" => return "number",
                "bool" => return "boolean",
                "PathBuf" => return "string",
                "Vec" => return "array",
                "Option" => {
                    // Extract inner type
                    if let PathArguments::AngleBracketed(AngleBracketedGenericArguments { args, .. }) = &segment.arguments {
                        if let Some(GenericArgument::Type(inner)) = args.first() {
                            return type_to_json_type(inner);
                        }
                    }
                    return "string";
                }
                _ => {}
            }
        }
    }
    "string"
}

// ── attribute parsing ────────────────────────────────────────────────────────

struct ToolAttrs {
    description: Option<String>,
}

impl ToolAttrs {
    fn from_attrs(attrs: &[Attribute]) -> Self {
        let mut description = None;
        for attr in attrs {
            if !attr.path().is_ident("tool") {
                continue;
            }
            if let Meta::NameValue(MetaNameValue { path, value, .. }) = &attr.meta {
                if path.is_ident("description") {
                    if let Expr::Lit(ExprLit { lit: Lit::Str(lit), .. }) = value {
                        description = Some(lit.value());
                    }
                }
            }
        }
        Self { description }
    }
}

struct FieldInfo {
    ident: Option<syn::Ident>,
    name: String,
    ty: Type,
    required: bool,
    description: Option<String>,
    default: Option<String>,
}

impl FieldInfo {
    fn from_field(field: &syn::Field) -> Self {
        let ident = field.ident.clone();
        let name = field.ident.as_ref().unwrap().to_string();
        let ty = field.ty.clone();
        let mut required = true;
        let mut description = None;
        let mut default = None;

        for attr in &field.attrs {
            if !attr.path().is_ident("tool") {
                continue;
            }
            if let Meta::NameValue(MetaNameValue { path, value, .. }) = &attr.meta {
                if path.is_ident("description") {
                    if let Expr::Lit(ExprLit { lit: Lit::Str(lit), .. }) = value {
                        description = Some(lit.value());
                    }
                } else if path.is_ident("default") {
                    if let Expr::Lit(ExprLit { lit: Lit::Str(lit), .. }) = value {
                        default = Some(lit.value());
                        required = false;
                    }
                }
            }
        }

        // Check if type is Option<T>
        if let Type::Path(type_path) = &ty {
            if let Some(segment) = type_path.path.segments.last() {
                if segment.ident == "Option" {
                    required = false;
                }
            }
        }

        Self {
            ident,
            name,
            ty,
            required,
            description,
            default,
        }
    }
}
