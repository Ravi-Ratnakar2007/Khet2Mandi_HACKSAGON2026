import pandas as pd
from geopy.geocoders import Nominatim
from time import sleep

MANDIS = [
"Ajmer","Alwar","Ambala","Amritsar","Anupgarh","Balotra","Banswara","Baran","Barmer","Barnala",
"Beawar","Bharatpur","Bhatinda","Bhilwara","Bhiwani","Bikaner","Bundi","Chittorgarh","Churu","Dausa",
"Deedwana Kuchaman","Deeg","Dholpur","Dudu","Dungarpur","Faridabad","Faridkot","Fatehabad","Fatehgarh",
"Fazilka","Ferozpur","Ganganagar","Gangapur City","Gurdaspur","Gurgaon","Hanumangarh","Hissar","Hoshiarpur",
"Jaipur","Jaipur Rural","Jaisalmer","Jalandhar","Jalore","Jhafarapatan","Jhajar","Jhalawar","Jhunjhunu",
"Jind","Jodhpur","Jodhpur Rural","Kaithal","Kapurthala","Karauli","Karnal","Kekri","Khairthal Tijara",
"Kota","Kotputli- Behror","Kurukshetra","Ludhiana","Mahendragarh-Narnaul","Mansa","Mewat","Moga",
"Mohali","Muktsar","Nagaur","Nawanshahr","Neem Ka Thana","Pali","Palwal","Panchkula","Panipat",
"Pathankot","Patiala","Phalodi","Pratapgarh","Rajsamand","Rewari","Rohtak","Ropar (Rupnagar)",
"Sanchore","Sangrur","Shahpura","Sikar","Sirohi","Sirsa","Sonipat","Swai Madhopur","Tarntaran",
"Tonk","Udaipur","Yamuna Nagar"
]

geolocator = Nominatim(user_agent="agri_ml_pipeline")

coords = []

for mandi in MANDIS:
    try:
        location = geolocator.geocode(f"{mandi}, India")
        
        if location:
            coords.append({
                "Market": mandi.lower(),
                "lat": location.latitude,
                "lon": location.longitude
            })
            print(mandi, location.latitude, location.longitude)
        else:
            print("Not found:", mandi)

        sleep(1)

    except:
        print("Error:", mandi)

df = pd.DataFrame(coords)

df.to_csv("processing/market_coordinates.csv", index=False)

print("Saved market_coordinates.csv")