
import requests
from bs4 import BeautifulSoup
import time
import re
import unicodedata

REQUEST_URL = 'https://airdoor.jp/list?li=d-91&p={}'

res = requests.get(REQUEST_URL)
max_pages = 10

# 複数ページの情報をまとめて取得
data_samples = []

for page in range(1, max_pages + 1):
    # ページ情報
    url = REQUEST_URL.format(page)
    response = requests.get(url)
    soup = BeautifulSoup(response.content,  'lxml')
    time.sleep(1)

    # 物件情報リストを指定
    mother = soup.find_all(class_='PropertyPanel_propertyPanel__8oJ13')

    # 物件ごとの処理
    for child in mother:

        # 建物情報
        data_home = []

        def extract_room_info(room_info):
        # 部屋番号、間取り、広さ、方角を正規表現で抽出
            room_matches = re.match(r'(\d+)号室 \/ (\S+) \/ (\d+(\.\d+)?)㎡ \/ (.+)', room_info)

            if room_matches:
            # room_numberのクレンジング処理
                room_number_raw = room_matches.group(1)
                room_number = str(int(room_number_raw))  # 半角数字に変換
                return room_number, room_matches.group(2), room_matches.group(3), room_matches.group(5)
            else:
                return "", "", "", ""

        def extract_address_info(building_info):
        # 住所情報を正規表現で抽出
            address_matches = re.findall(r'(東京都|大阪府|京都府|などの都道府県の正規表現)(.*?)(\d+丁目|$)', building_info)

            if address_matches:
                prefecture = address_matches[0][0]
                city = address_matches[0][1].replace('の', '')  # 区市町村から不要な文字を削除

                #"宅配ボックス" もしくは "エレベーター" が含まれている場合は削除
                keywords_to_remove = ['宅配ボックス', 'エレベーター']
                for keyword in keywords_to_remove:
                    city = city.replace(keyword, '')

                address = address_matches[0][2]
                return prefecture, city, address
            else:
                return "", "", ""

        # 建物名
        building_info = child.find(class_='PropertyPanelBuilding_buildingTitle__tuPqN').text
        building_info_parts = re.split(r'\s+', building_info)  # 空白で分割
        vacancy_info = building_info_parts[0] if building_info_parts else ""
        building_name = building_info_parts[1] if len(building_info_parts) > 1 else ""

        data_home.append(vacancy_info)
        data_home.append(building_name)

        # 家賃、管理費
        rent_info = child.find(class_='PropertyPanelRoom_rentPrice__XdPUp').text
        rent_matches = re.match(r'(\d+,\d+)円 \((.+)\)', rent_info)
        rent = rent_matches.group(1) if rent_matches else ""
        management_fee = rent_matches.group(2) if rent_matches else ""

        # 1. rent の末尾に「円」を付ける
        #rent += "円"

        # 2. management_fee から文頭の「管理費」を取り除く
        management_fee = management_fee.replace("管理費", "").replace("円", "")

        # 3. rent と management_fee を足して total_fee を項目として追加する
        total_fee = str(int(rent.replace("円", "").replace(",", "")) + int(management_fee.replace(",", ""))) if rent and management_fee else "0"

        # 4. 管理費にも円を付け足す
        #management_fee += "円"

        data_home.append(rent)
        data_home.append(management_fee)
        data_home.append(total_fee)

        # 部屋情報（間取り）
        room_info = child.find(class_='is-ml5').text

        # 部屋情報を正規表現で抽出
        room_number, layout, area, direction = extract_room_info(room_info)

        # 最寄り駅のアクセス、住所、建物情報、築年数、階数
        building_info = child.find(class_='PropertyPanelBuilding_buildingInformationSection__deSLp').text

        # 住所情報を正規表現で抽出
        prefecture, city, address = extract_address_info(building_info)

        # 正規表現を使って情報を抽出
        walk_time_matches = re.findall(r'徒歩(\d+)分', building_info)
        delivery_box_matches = re.findall(r'宅配ボックス', building_info)
        parking_matches = re.findall(r'駐車場あり', building_info)
        elevator_matches = re.findall(r'エレベーター', building_info)

        # 住所、徒歩、宅配ボックス、駐車場あり、エレベーターの情報を取得
        walk_time = walk_time_matches[0] if walk_time_matches else ""
        delivery_box = "〇" if delivery_box_matches else ""
        parking = "〇" if parking_matches else ""
        elevator = "〇" if elevator_matches else ""

        # 最寄り駅のアクセス、住所、建物情報、築年数、階数
        building_info2 = child.find(class_='PropertyPanelBuilding_buildingInformation__bL4Gu is-pc-only').text

        # 最寄り駅
        def extract_station_info(station_info):
        # 正規表現で路線名、駅名、徒歩情報を抽出
            station_matches = re.findall(r'(.+?)\s+(.+?)\s+(?:徒歩(\d+)分)?', station_info)

            if station_matches:
                station_info_list = [(line, station, int(walk) if walk else 0) for line, station, walk in station_matches]
                return station_info_list
            else:
                return []

        station_info_list = extract_station_info(building_info2)

        # 築年数、階数、材質情報を正規表現で抽出
        built_year_matches = re.search(r'築(\d+年|新築)', building_info2)
        floors_matches = re.search(r'(\d+)階建', building_info2)
        material_matches = re.search(r'(鉄筋コンクリート|鉄骨造|木造|軽量鉄骨|その他)', building_info2)

        # 築年数の文字列から全角数字を半角数字に変換し、"年"を取り除く関数
        def process_built_year(built_year_str):
        # 全角数字を半角数字に変換
            normalized_str = unicodedata.normalize('NFKC', built_year_str)
        # "年"を取り除く
            cleaned_str = normalized_str.replace("年", "")
            return cleaned_str

        # 築年数、階数、材質情報を変数に格納
        built_year = process_built_year(built_year_matches.group(1)) if built_year_matches else "0"
        floors = floors_matches.group(1) if floors_matches else ""
        material = material_matches.group(1) if material_matches else ""

        # お得情報(項目)
        sale_info_element = child.find(class_='PropertyPanelRoom_isRed__0DqN8 PropertyPanelRoom_isBold__J8dEF')
        sale_info = sale_info_element.text if sale_info_element else ""

        # お得情報(額面)
        sale_info_element_2 = child.find(class_='PropertyPanelRoom_strikeText__ru8wH')
        sale_info_2 = sale_info_element_2.text if sale_info_element_2 else ""
        sale_info_2 = re.sub(r'円', '', sale_info_2)

        # お得情報(概要)を取得
        sale_info_element_3 = child.find(class_='PropertyPanelRoom_freerentTagBlock__K141G')
        sale_info_3 = sale_info_element_3.text if sale_info_element_3 else ""

        # お得情報(星)を取得
        stars_container = child.find(class_='InitialCostScore_starsContainer__xsree')

        # おすすめ度の星の数を数える
        recommended_stars = stars_container.find_all('span', class_='Stars_starSvg__6zBqF Stars_active__t_wHp') if stars_container else []
        not_recommended_stars = stars_container.find_all('span', class_='Stars_starSvg__6zBqF Stars_inActive__b_Usx') if stars_container else []

        # おすすめ度の数をカウント
        recommended_count = len(recommended_stars)
        not_recommended_count = len(not_recommended_stars)

        # カラムに情報を追加
        data_home.extend([room_number, layout, area, direction, prefecture, station_info_list, city, address, walk_time, delivery_box, parking, elevator, built_year, floors, material, sale_info , sale_info_2, sale_info_3, recommended_count])

        # 物件情報と部屋情報をくっつける
        data_samples.append(data_home)

#Pandas-------------------------------
import pandas as pd
df = pd.DataFrame(data_samples)

#カラム名を付ける
df = df.rename(columns = {0:'空室情報',1:'建物名',2:'家賃',3:'管理費',4:'合計金額',5:'部屋No',6:'間取り',7:'面積',8:'方角',9:'都道府県',10:'最寄り駅',11:'市区町村',12:'丁目',13:'駅徒歩',14:'宅配ボックス',15:'駐車場',16:'エレベーター',17:'築年情報',18:'物件階数',19:'材質',20:'お得情報',21:'値引金額',22:'追加セールスポイント',23:'おすすめ度'})

#データの整形
# 最寄り駅のリストを文字列に変換
df['最寄り駅'] = df['最寄り駅'].apply(lambda x: ', '.join(map(str, x)) if isinstance(x, (list, tuple)) else x)

# '面積'が欠損している行を削除
df = df.dropna(subset=['面積'])

# 重複が削除できていないようであれば、再度実行
df = df.drop_duplicates(subset=['建物名', '合計金額', '面積', '部屋No'])
df.drop_duplicates(inplace=True)

#Google Sperad Sheet-------------------------------
import gspread
from google.auth import exceptions
from google.oauth2.service_account import Credentials

# Google Spread Sheetの認証情報を取得
credentials = Credentials.from_service_account_file('xenon-effect-411113-926fae6f3bd2.json', scopes=['https://www.googleapis.com/auth/spreadsheets'])
gc = gspread.authorize(credentials)

# Google Spread SheetのURL
spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1JT6fZwPAl_LWajo7iqqCjH4MKsYYW5dXgNxQQxId7ew/edit#gid=0'

# スプレッドシートを開く
worksheet = gc.open_by_url(spreadsheet_url).sheet1

# データフレームをGoogle Spread Sheetにアップロード
data = df.values.tolist()
worksheet.clear()  # シートをクリア
worksheet.append_rows(data)  # データを追加

