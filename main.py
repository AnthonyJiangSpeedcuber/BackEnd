import fastapi, pydantic, uvicorn
from supabase import create_client
 
SUPABASE_URL = "https://ptjzlkfopudoowqygbtw.supabase.co"
SUPABASE_KEY = "sb_publishable_bUCQLgx2FLX4o3TxkRnoJQ_wdD6gsGj"
 
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
 
app = FastAPI()
 
 
@app.get("/")
def root():
    return {"status": "online"}
 
 
@app.get("/users")
def get_users():
    response = supabase.table("users").select("*").execute()
    return response.data