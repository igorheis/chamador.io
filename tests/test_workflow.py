import unittest
import os
import tempfile
from fastapi.testclient import TestClient

_test_db = tempfile.NamedTemporaryFile(prefix="chamador-test-", suffix=".db", delete=False)
_test_db.close()
os.environ["CHAMADOR_DATABASE_URL"] = f"sqlite:///{_test_db.name}"
from backend.main import app

class CallWorkflowTests(unittest.TestCase):
    def setUp(self): self.client=TestClient(app)
    def test_parallel_requests_and_independent_completion(self):
        made=[]
        for room,kind in [(1,"Água"),(2,"Anestesia"),(3,"Gazes"),(3,"Valo"),(7,"Limpeza")]:
            r=self.client.post("/api/solicitacoes",json={"consultorio_id":room,"tipo":kind})
            self.assertEqual(r.status_code,201);made.append(r.json())
        ids={c["id"] for c in made}
        active=self.client.get("/api/solicitacoes").json()
        self.assertTrue(ids.issubset({c["id"] for c in active}))
        room3=[c for c in active if c["consultorio_id"]==3 and c["id"] in ids]
        self.assertEqual(len(room3),2)
        completed=self.client.post(f"/api/solicitacoes/{room3[0]['id']}/concluir").json()
        self.assertEqual(completed["status"],"concluido")
        active2=self.client.get("/api/solicitacoes").json()
        self.assertNotIn(completed["id"],{c["id"] for c in active2})
        self.assertIn(room3[1]["id"],{c["id"] for c in active2})
        history=self.client.get("/api/solicitacoes?status=concluidos").json()
        self.assertIn(completed["id"],{c["id"] for c in history})
        self.assertIsNotNone(completed["data_hora_conclusao"])
        self.assertIsNotNone(completed["tempo_atendimento"])
        for c in made: self.client.post(f"/api/solicitacoes/{c['id']}/concluir")

    def test_claim_and_websocket_snapshot_and_updates(self):
        with self.client.websocket_connect("/ws") as ws:
            with self.client.websocket_connect("/ws") as second_panel:
                self.assertEqual(ws.receive_json()["event"],"snapshot")
                self.assertEqual(second_panel.receive_json()["event"],"snapshot")
                call=self.client.post("/api/solicitacoes",json={"consultorio_id":1,"tipo":"Abridor"}).json()
                for panel in (ws,second_panel):
                    event=panel.receive_json();self.assertEqual(event["event"],"created");self.assertEqual(event["request"]["id"],call["id"])
                assistants=self.client.get("/api/meta").json()["auxiliares"]
                claimed=self.client.post(f"/api/solicitacoes/{call['id']}/assumir",json={"auxiliar_id":assistants[0]["id"]})
                self.assertEqual(claimed.status_code,200)
                for panel in (ws,second_panel):
                    update=panel.receive_json();self.assertEqual(update["event"],"updated");self.assertEqual(update["request"]["status"],"em_atendimento")
                done=self.client.post(f"/api/solicitacoes/{call['id']}/concluir").json()
                for panel in (ws,second_panel): self.assertEqual(panel.receive_json()["event"],"completed")
                self.assertEqual(done["status"],"concluido")

if __name__=="__main__": unittest.main()
