import google.generativeai as genai
import json, os, urllib.parse

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

def get_home_recommendations(budget_input):
    prompt = f"Budget {budget_input.total_budget} for {budget_input.room_type}. Suggest 3 products. Return JSON {{'home_recommendations': [{{'name':'','price_in_inr':0,'search_terms':''}}]}}"
    res = model.generate_content(prompt)
    try:
        result = json.loads(res.text.replace("```json","").replace("```",""))
    except:
        result = {"home_recommendations": [{"name":"Modern Sofa","price_in_inr":8000,"search_terms":"sofa for living room"}]}
    for item in result.get("home_recommendations", []):
        s = item.get("search_terms","home decor")
        item["shopping_links"] = {
            "amazon": f"https://www.amazon.in/s?k={urllib.parse.quote(s)}",
            "flipkart": f"https://www.flipkart.com/search?q={urllib.parse.quote(s)}",
            "ikea": f"https://www.ikea.com/in/en/search/?q={urllib.parse.quote(s)}"
        }
    return result

def get_party_recommendations(budget_input):
    prompt = f"Party {budget_input.party_type} budget {budget_input.total_budget} guests {budget_input.num_guests}. Return JSON"
    res = model.generate_content(prompt)
    try: return json.loads(res.text.replace("```json","").replace("```",""))
    except: return {"party_recommendations": []}

def get_jewelry_recommendations(budget_input, image_path=None):
    prompt = f"Jewelry budget {budget_input.total_budget} occasion {budget_input.occasion}. Return JSON with search_terms"
    if image_path and os.path.exists(image_path):
        img = genai.upload_file(image_path)
        res = model.generate_content([prompt, img])
    else:
        res = model.generate_content(prompt)
    try: result = json.loads(res.text.replace("```json","").replace("```",""))
    except: result = {"jewelry_recommendations": [{"name":"Gold Necklace","price_in_inr":15000,"search_terms":"gold necklace"}]}
    for item in result.get("jewelry_recommendations", []):
        s = item.get("search_terms","gold necklace")
        item["shopping_links"] = {
            "amazon": f"https://www.amazon.in/s?k={urllib.parse.quote(s)}",
            "tanishq": f"https://www.tanishq.co.in/search?q={urllib.parse.quote(s)}",
            "bluestone": f"https://www.bluestone.com/search.html?search?q={urllib.parse.quote(s)}"
        }
    return result