import gspread
import pandas as pd
from google.auth import exceptions
from google.oauth2.service_account import Credentials
import streamlit as st
from PIL import Image  # イメージを表示

# Google Spread Sheetからデータを読み込む関数
def load_data_from_spreadsheet(spreadsheet_url):
    credentials = Credentials.from_service_account_file('xenon-effect-411113-926fae6f3bd2.json',
                                                        scopes=['https://www.googleapis.com/auth/spreadsheets'])
    gc = gspread.authorize(credentials)
    worksheet = gc.open_by_url(spreadsheet_url).sheet1
    data = worksheet.get_all_values()
    return pd.DataFrame(data[1:], columns=data[0])

# Streamlitアプリの実装
def main():
    # Google Spread Sheetからデータを読み込む
    spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1JT6fZwPAl_LWajo7iqqCjH4MKsYYW5dXgNxQQxId7ew/edit#gid=0'
    df = load_data_from_spreadsheet(spreadsheet_url)

    # 各数値型の列を適切な型に変換
    df['合計金額'] = df['合計金額'].fillna(0).astype(int)
    df['駅徒歩'] = df['駅徒歩'].fillna(0).astype(int)
    df['築年情報'] = df['築年情報'].fillna(0).astype(int)
    df['面積'] = pd.to_numeric(df['面積'].replace('', pd.NA), errors='coerce')

    # Streamlitアプリの表示
    st.title('おとりなし不動産')
    st.markdown("本アプリでは、おとり物件なしで今だけのお値引きがされた物件情報をお届けしています。<br>物件は山手線エリアを中心に紹介してます。", unsafe_allow_html=True)

    image = Image.open('image1.png')  # 画像挿入
    st.image(image, caption=None)

    # タグの選択リストを作成
    LOCATION = ["新宿駅", "代々木駅", "原宿駅", "渋谷駅", "恵比寿駅", "目黒駅", "五反田駅", "大崎駅", "品川駅", "高輪ゲートウェイ駅", "田町駅",
                "浜松町駅", "新橋駅", "有楽町駅", "東京駅", "神田駅", "秋葉原駅", "御徒町駅", "上野駅", "鶯谷駅", "日暮里駅", "西日暮里駅", "田端駅",
                "駒込駅", "巣鴨駅", "大塚駅", "池袋駅", "目白駅", "高田馬場駅", "新大久保駅"]
    PLAN = ["1R", "1K", "1DK", "1LDK", "2K", "2LDK", "3DK", "3LDK"]

    # サイドバーに最寄り駅のマルチ選択リストを表示
    selected_locations = st.sidebar.multiselect("最寄り駅を選択してください", LOCATION)

    # 最寄り駅のタプルから駅名の文字列だけを取り出してソート
    selected_range = st.sidebar.slider("賃料（管理費込）", min_value=0, max_value=50, value=(0, 500000),step=1000)
    selected_plan = st.sidebar.multiselect("希望する間取りを選んでください", PLAN)
    selected_size = st.sidebar.slider("部屋の広さを選択してください", min_value=0, max_value=100, value=(20, 80))
    selected_wark = st.sidebar.slider("駅徒歩の距離を選択してください", min_value=1, max_value=20, value=(5, 15))

    # 「検索する」ボタン
    search_button_clicked = st.sidebar.button("検索する")

    # 選択された範囲内の条件でデータを絞り込む
    filtered_data = df[
        (df['最寄り駅'].apply(lambda x: any(station_name in x for station_name in selected_locations))) &
        (df['合計金額'].astype(int) >= selected_range[0]) &
        (df['合計金額'].astype(int) <= selected_range[1]) &
        ((df['間取り'].isin(selected_plan)) | (df['間取り'].isna())) &  # 間取りが空欄でも対応できるように修正
        (df['面積'].astype(float).fillna(0) >= selected_size[0]) &
        (df['面積'].astype(float).fillna(0) <= selected_size[1]) &
        (df['駅徒歩'].astype(int) >= selected_wark[0]) &
        (df['駅徒歩'].astype(int) <= selected_wark[1])
    ]

    # 選択された列のサブセットを表示
    selected_columns = ['おすすめ度', '値引金額', '建物名', '家賃', '管理費', '間取り', '面積', '最寄り駅', '駅徒歩', '築年情報', '材質']  # 適切な列名に置き換えてください
    # 条件分岐内でのみ st.dataframe(filtered_data) を実行
    if search_button_clicked:
        st.write(filtered_data[selected_columns])
    elif not filtered_data.empty:  # 検索前に物件があれば表示
        st.write(df[selected_columns])

# Streamlitアプリを実行
if __name__ == "__main__":
    main()
