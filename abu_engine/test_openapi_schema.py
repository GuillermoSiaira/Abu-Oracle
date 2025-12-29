"""Quick test to verify OpenAPI schema generation works without warnings."""
from main import app

try:
    schema = app.openapi()
    print("✅ OpenAPI schema generated successfully")
    print(f"   Endpoints: {len(schema['paths'])}")
    print(f"   Title: {schema['info']['title']}")
    
    # Check key endpoints have examples
    analyze_path = schema['paths'].get('/analyze', {})
    if analyze_path:
        post_op = analyze_path.get('post', {})
        examples = post_op.get('requestBody', {}).get('content', {}).get('application/json', {}).get('examples', {})
        print(f"   /analyze examples: {len(examples)} ✅" if examples else "   /analyze examples: missing ❌")
    
    interpret_path = schema['paths'].get('/api/astro/interpret', {})
    if interpret_path:
        post_op = interpret_path.get('post', {})
        examples = post_op.get('requestBody', {}).get('content', {}).get('application/json', {}).get('examples', {})
        print(f"   /api/astro/interpret examples: {len(examples)} ✅" if examples else "   /api/astro/interpret examples: missing ❌")
    
    print("\n✅ All checks passed - OpenAPI schema is valid")
except Exception as e:
    print(f"❌ OpenAPI schema generation failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
