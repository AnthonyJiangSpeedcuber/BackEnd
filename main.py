from typing import List, Optional
import hashlib

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client
import uvicorn

SUPABASE_URL = "https://ptjzlkfopudoowqygbtw.supabase.co"
SUPABASE_KEY = "YOUR_SUPABASE_ANON_KEY"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


class RegisterUser(BaseModel):
    email: str
    password: str
    name: str


class MenuItem(BaseModel):
    item_name: str
    price: Optional[float] = None


class Restaurant(BaseModel):
    restaurant_name: str
    restaurant_type: str
    menu_items: List[MenuItem]


@app.post("/register")
def register(user: RegisterUser):
    auth = supabase.auth.sign_up(
        {
            "email": user.email,
            "password": user.password,
            "options": {
                "data": {
                    "name": user.name
                }
            }
        }
    )

    if auth.user is None:
        raise HTTPException(status_code=400, detail="Registration failed")
     
    hashed_password = hash_password(user.password)

    supabase.table("users").insert(
        {
            "id": auth.user.id,
            "name": user.name,
            "email": user.email,
            "password_hash": hashed_password,
        }
    ).execute()

    return {
        "id": auth.user.id,
        "emailg": auth.user.email,
        "name": user.name,
    }


@app.post("/restaurants")
def add_restaurant(restaurant: Restaurant):
    response = supabase.table("restaurants").insert(
        {
            "restaurant_name": restaurant.restaurant_name,
            "restaurant_type": restaurant.restaurant_type,
        }
    ).execute()

    if not response.data:
        raise HTTPException(status_code=400, detail="Restaurant creation failed")

    restaurant_id = response.data[0]["id"]

    menu_rows = [
        {
            "restaurant_id": restaurant_id,
            "item_name": item.item_name,
            "price": item.price,
        }
        for item in restaurant.menu_items
    ]

    if menu_rows:
        supabase.table("menu_items").insert(menu_rows).execute()

    return {
        "id": restaurant_id,
        "restaurant_name": restaurant.restaurant_name,
        "restaurant_type": restaurant.restaurant_type,
        "menu_items": restaurant.menu_items,
    }


@app.get("/restaurants")
def get_restaurants():
    restaurants = supabase.table("restaurants").select("*").execute()

    result = []

    for restaurant in restaurants.data:
        menu = (
            supabase.table("menu_items")
            .select("*")
            .eq("restaurant_id", restaurant["id"])
            .execute()
        )

        result.append(
            {
                "id": restaurant["id"],
                "restaurant_name": restaurant["restaurant_name"],
                "restaurant_type": restaurant["restaurant_type"],
                "menu_items": menu.data,
            }
        )

    return result


@app.get("/restaurants/{restaurant_id}")
def get_restaurant(restaurant_id: str):
    restaurant = (
        supabase.table("restaurants")
        .select("*")
        .eq("id", restaurant_id)
        .execute()
    )

    if not restaurant.data:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    menu = (
        supabase.table("menu_items")
        .select("*")
        .eq("restaurant_id", restaurant_id)
        .execute()
    )

    return {
        "id": restaurant.data[0]["id"],
        "restaurant_name": restaurant.data[0]["restaurant_name"],
        "restaurant_type": restaurant.data[0]["restaurant_type"],
        "menu_items": menu.data,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)