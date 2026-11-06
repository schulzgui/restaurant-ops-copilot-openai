"""Protocol fixtures exclusively for tests, never available in the application CLI."""
import json
import re

def tool(name,args,number=1):
    return {"type":"function_call","name":name,"arguments":json.dumps(args),"call_id":f"call-{number}","id":f"fc-{number}"}
def response(output):
    return {"status":"completed","output":output,"usage":{"input_tokens":10,"output_tokens":5}}
def message(text,policies=None,orders=None):
    final={"summary":text,"policy_ids":policies or [],"order_ids":orders or [],"limitations":["Resposta controlada de teste; não é avaliação de LLM."]}
    return {"type":"message","role":"assistant","content":[{"type":"output_text","text":json.dumps(final)}]}
class ScriptedProvider:
    mode="test_fixture";model="test-fixture-not-a-real-model"
    def __init__(self,outputs):self.outputs=iter(outputs);self.histories=[]
    def respond(self,history,tools,instructions):
        self.histories.append(list(history));return response(next(self.outputs))
class ScenarioFixture:
    mode="test_fixture";model="test-fixture-not-a-real-model"
    def respond(self,history,tools,instructions):
        prompt=history[0]["content"].lower()
        seen=sum(i.get("type")=="function_call_output" for i in history)
        plan=[]
        if any(x in prompt for x in ['ignore','reembol']):pass
        elif 'políticas' in prompt:plan=[('search_policies',{'query':prompt})]
        elif 'urgentes' in prompt:plan=[('list_orders',{'scope':'urgent'})]
        else:
            ids=re.findall(r'SYN-\d{3}',prompt.upper())
            if ids:
                oid=ids[0];plan=[('get_order',{'order_id':oid})]
                mapping={'SYN-001':('delay_update','P-DELAY'),'SYN-002':('escalate','P-DELAY'),'SYN-003':('escalate','P-SAFETY'),'SYN-004':('missing_review','P-MISSING')}
                if oid in mapping and any(x in prompt for x in ['prepare','proposta']):
                    template,policy=mapping[oid]
                    plan += [('get_policy',{'policy_id':policy}),('propose_action',{'order_id':oid,'template':template,'policy_id':policy})]
        if seen<len(plan):return response([tool(*plan[seen],number=seen+1)])
        return response([message('Execução controlada finalizada; propostas exigem revisão.')])
