import inspect
import backend.core.adaptive_agent as aa

src = inspect.getsource(aa.AdaptiveAgent.run)
print('zoom assignment present:', 'required_integration = "zoom"' in src)
start = src.find('required_integration = None')
print(src[start:start+900])
