"""Comprehensive E2E test for Sovereign Agent Stack."""
from sas.core.scoring import score_config, generate_report
from sas.core.config import SASConfig, parse_sas_yaml, ModelConfig, SubstrateType, MemoryProvider, AuthBroker, LongTermProvider, Ownership
from sas.layers.knowledge import CompileTimeKnowledge
from sas.layers.auth import LocalAuthBroker, Credentials, Request
from sas.layers.payments import VirtualCardAdapter, MPPAdapter, PaymentRequirement, SpendingLimit
from sas.plugins import PluginRegistry, LayerPlugin, PluginSource, register_plugin, unregister_plugin, get_plugin, list_plugins
from sas.mcp_server import check_sovereignty, query_knowledge, pay_for_resource, handle_mcp_request
from pathlib import Path
import tempfile, os

passed = 0
failed = 0

def run_test(name, fn):
    global passed, failed
    try:
        fn()
        print(f'  ✓ {name}')
        passed += 1
    except Exception as e:
        print(f'  ✗ {name}: {e}')
        failed += 1

print('=== 1. Scoring Engine ===')
def t1():
    config = SASConfig(
        model_primary=ModelConfig(provider='ollama', name='llama3.1:8b', location='local'),
        substrate=SubstrateType.LOCAL_DOCKER,
        memory_short_term=MemoryProvider.LOCAL_RAG,
        memory_long_term=LongTermProvider.COMPILE_TIME_GRAPH,
        auth_broker=AuthBroker.LOCAL_MCP_GATEWAY,
    )
    report = generate_report(config)
    assert report.score == 1.0
    assert report.verdict == 'Fully Sovereign'
run_test('Fully sovereign config', t1)

def t2():
    rented_config = SASConfig(
        model_primary=ModelConfig(provider='openai', name='gpt-4o', location='api'),
        substrate=SubstrateType.ORGO_CLOUD,
        memory_short_term=MemoryProvider.HONCHO_CLOUD,
        memory_long_term=LongTermProvider.RETRIEVAL_ONLY,
        auth_broker=AuthBroker.COMPOSIO,
    )
    report = generate_report(rented_config)
    assert report.verdict == 'Rented'
run_test('Rented config', t2)

def t3():
    config = SASConfig(
        model_primary=ModelConfig(provider='ollama', name='llama3.1:8b', location='local'),
    )
    config.overrides = {'layer_5': Ownership.OWNED}
    report = generate_report(config)
    assert report.score == 1.0
run_test('Manual override', t3)

print('=== 2. Knowledge Graph ===')
def t4():
    with tempfile.TemporaryDirectory() as tmpdir:
        kd = Path(tmpdir) / 'knowledge'
        kd.mkdir()
        (kd / 'intro.md').write_text('# Introduction\nThe [[Sovereign Agent Stack]] intro.\n[[ARGO]] is the harness.')
        (kd / 'arch.md').write_text('# Architecture\nSee [[intro]].')
        (kd / 'nested').mkdir()
        (kd / 'nested' / 'deep.md').write_text('Deep [[intro]].')
        kg = CompileTimeKnowledge()
        graph = kg.compile(kd)
        assert len(graph.nodes) >= 3
        assert len(graph.edges) >= 2
run_test('Compile from directory', t4)

def t5():
    with tempfile.TemporaryDirectory() as tmpdir:
        kd = Path(tmpdir) / 'knowledge'
        kd.mkdir()
        (kd / 'test.md').write_text('# Test\nContent about sovereign architecture.')
        kg = CompileTimeKnowledge()
        graph = kg.compile(kd)
        results = kg.query(graph, 'sovereign')
        assert len(results) >= 1
run_test('Query by content', t5)

def t6():
    with tempfile.TemporaryDirectory() as tmpdir:
        kd = Path(tmpdir) / 'knowledge'
        kd.mkdir()
        (kd / 'a.md').write_text('# Alpha\nLinks to [[beta]].')
        (kd / 'b.md').write_text('# Beta\nLinks to [[alpha]].')
        kg = CompileTimeKnowledge()
        graph = kg.compile(kd)
        diff = kg.diff(graph, graph)
        assert len(diff.added_nodes) == 0
        assert len(diff.removed_nodes) == 0
        audit = kg.audit(graph)
        assert audit.total_nodes == 4  # Alpha, Beta + wikilink targets beta, alpha
run_test('Diff and audit', t6)

print('=== 3. Auth Broker ===')
def t7():
    with tempfile.TemporaryDirectory() as tmpdir:
        vp = os.path.join(tmpdir, 'vault.db')
        broker = LocalAuthBroker(store_path=vp, encryption_key='test-key')
        broker.register_tool('github', Credentials(
            tool_name='github', auth_type='oauth', token='ghp_test123', scopes=['repo']
        ))
        broker.register_tool('slack', Credentials(
            tool_name='slack', auth_type='api_key', token='xoxb-test'
        ))
        tools = broker.list_tools()
        assert len(tools) == 2
        creds = broker.get_credentials('github')
        assert creds.token == 'ghp_test123'
        assert creds.scopes == ['repo']
run_test('Register and get credentials', t7)

def t8():
    with tempfile.TemporaryDirectory() as tmpdir:
        vp = os.path.join(tmpdir, 'vault.db')
        broker = LocalAuthBroker(store_path=vp, encryption_key='test-key')
        broker.register_tool('github', Credentials(
            tool_name='github', auth_type='oauth', token='ghp_test123'
        ))
        def mock_http(req):
            from sas.layers.auth import Response
            return Response(200, {}, b'{}')
        req = Request(tool_name='github', method='GET', path='/user', headers={})
        resp = broker.call(req, mock_http)
        assert resp.status_code == 200
        audit = broker.audit()
        assert len(audit.entries) == 1
run_test('Call and audit', t8)

def t9():
    with tempfile.TemporaryDirectory() as tmpdir:
        vp = os.path.join(tmpdir, 'vault.db')
        broker = LocalAuthBroker(store_path=vp, encryption_key='test-key')
        broker.register_tool('github', Credentials(
            tool_name='github', auth_type='oauth', token='ghp_test123'
        ))
        broker.register_tool('slack', Credentials(
            tool_name='slack', auth_type='api_key', token='xoxb-test'
        ))
        broker.unregister_tool('slack')
        assert len(broker.list_tools()) == 1
run_test('Unregister', t9)

print('=== 4. Payments Adapters ===')
def t10():
    vc = VirtualCardAdapter(
        provider='ramp',
        limit=SpendingLimit(daily=500, per_transaction=200, currency='USD')
    )
    vc.pay(PaymentRequirement('openai', 50, 'USD', ['card'], 'one_shot', {}))
    vc.pay(PaymentRequirement('github', 30, 'USD', ['card'], 'one_shot', {}))
    assert vc.daily_spending == 80
    assert vc.remaining_daily == 420
run_test('Virtual card within limits', t10)

def t11():
    vc = VirtualCardAdapter(
        limit=SpendingLimit(daily=500, per_transaction=200, currency='USD')
    )
    try:
        vc.pay(PaymentRequirement('aws', 250, 'USD', ['card'], 'one_shot', {}))
        assert False, 'Should have raised'
    except ValueError:
        pass
run_test('Transaction limit enforced', t11)

def t12():
    vc = VirtualCardAdapter()
    try:
        vc.pay(PaymentRequirement('x', 50, 'USD', ['stablecoin'], 'one_shot', {}))
        assert False, 'Should have raised'
    except ValueError:
        pass
run_test('Method check enforced', t12)

def t13():
    mpp = MPPAdapter(
        settlement='stablecoin',
        limit=SpendingLimit(daily=1000, per_transaction=500, currency='USD')
    )
    r = mpp.pay(PaymentRequirement('anthropic', 100, 'USD', ['stablecoin'], 'one_shot', {}))
    assert r.status == 'completed'
    receipt = mpp.receipt(r.payment_id)
    assert receipt.resource == 'anthropic'
run_test('MPP stablecoin payment', t13)

def t14():
    mpp = MPPAdapter(
        settlement='card',
        limit=SpendingLimit(daily=1000, per_transaction=500, currency='USD')
    )
    r = mpp.pay(PaymentRequirement('vercel', 75, 'USD', ['card'], 'one_shot', {}))
    assert r.status == 'completed'
run_test('MPP card payment', t14)

def t15():
    mpp = MPPAdapter(
        settlement='bnpl',
        limit=SpendingLimit(daily=1000, per_transaction=500, currency='USD')
    )
    r = mpp.pay(PaymentRequirement('netlify', 50, 'USD', ['bnpl'], 'one_shot', {}))
    assert r.status == 'completed'
run_test('MPP BNPL payment', t15)

print('=== 5. Plugin System ===')
def t16():
    PluginRegistry.reset()
    register_plugin(LayerPlugin('auth_builtin', 'layer_7_auth', '1.0.0', source=PluginSource.BUILTIN))
    register_plugin(LayerPlugin('auth_pip', 'layer_7_auth', '1.0.0', source=PluginSource.PIP))
    register_plugin(LayerPlugin('auth_local', 'layer_7_auth', '1.0.0', source=PluginSource.LOCAL))
    best = get_plugin('layer_7_auth')
    assert best.name == 'auth_local'
    unregister_plugin('layer_7_auth')
    best = get_plugin('layer_7_auth')
    assert best is None
run_test('Plugin register/unregister', t16)

def t17():
    PluginRegistry.reset()
    register_plugin(LayerPlugin('p1', 'layer_7_auth', '1.0.0', source=PluginSource.BUILTIN))
    register_plugin(LayerPlugin('p2', 'layer_7_auth', '1.0.0', source=PluginSource.PIP))
    register_plugin(LayerPlugin('p3', 'layer_8_payments', '1.0.0', source=PluginSource.LOCAL))
    all_p = list_plugins()
    assert len(all_p) == 2  # Only 2 unique layers (auth + payments)
    auth_p = list_plugins('layer_7_auth')
    assert len(auth_p) == 1
run_test('Plugin listing and filtering', t17)

print('=== 6. MCP Server ===')
def t18():
    resp = check_sovereignty(config_path='/tmp/test-sas.yaml')
    assert resp['verdict'] == 'Fully Sovereign'
    assert resp['score'] == 1.0
run_test('check_sovereignty', t18)

def t19():
    with tempfile.TemporaryDirectory() as tmpdir:
        kd = Path(tmpdir) / 'knowledge'
        kd.mkdir()
        (kd / 'test.md').write_text('# Test\nContent about sovereign architecture.')
        results = query_knowledge(query='sovereign', source=str(kd))
        assert len(results) >= 1
run_test('query_knowledge', t19)

def t20():
    result = pay_for_resource(resource='test_service', price=25.0)
    assert result['status'] == 'completed'
    assert result['amount'] == 25.0
run_test('pay_for_resource', t20)

def t21():
    resp = handle_mcp_request({'tool': 'check_sovereignty', 'params': {'config_path': '/tmp/test-sas.yaml'}})
    assert 'result' in resp
    assert resp['result']['verdict'] == 'Fully Sovereign'
run_test('handle_mcp_request', t21)

print('=== 7. CLI + Config ===')
def t22():
    parsed = parse_sas_yaml(Path('/tmp/test-sas.yaml'))
    assert parsed.substrate == SubstrateType.LOCAL_DOCKER
    assert parsed.auth_broker == AuthBroker.LOCAL_MCP_GATEWAY
    assert parsed.memory_short_term == MemoryProvider.LOCAL_RAG
run_test('parse_sas_yaml', t22)

def t23():
    config = SASConfig(
        model_primary=ModelConfig(provider='ollama', name='llama3.1:8b', location='local'),
    )
    report = generate_report(config, previous_score=0.8)
    assert abs(report.drift - 0.2) < 1e-9
run_test('Drift detection', t23)

print()
print(f'Results: {passed} passed, {failed} failed')
if failed == 0:
    print('╔══════════════════════════════════════════════════════════════╗')
    print('║  ALL E2E TESTS PASSED — 7/7 layers operational             ║')
    print('╚══════════════════════════════════════════════════════════════╝')
else:
    print(f'FAILED: {failed} tests')
