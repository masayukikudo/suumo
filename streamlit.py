import requests
import gspread
from google.auth import exceptions
from google.oauth2.service_account import Credentials

# Google Spread Sheetからデータを読み込む関数
def load_data_from_spreadsheet(spreadsheet_url):
    credentials = Credentials.from_service_account_file('xenon-effect-411113-926fae6f3bd2.json', scopes=['https://www.googleapis.com/auth/spreadsheets'])
    gc = gspread.authorize(credentials)
    worksheet = gc.open_by_url(spreadsheet_url).sheet1
    data = worksheet.get_all_values()
    return pd.DataFrame(data[1:], columns=data[0])

# Streamlitアプリの実装
def main():
    # Google Spread Sheetからデータを読み込む
    spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1JT6fZwPAl_LWajo7iqqCjH4MKsYYW5dXgNxQQxId7ew/edit#gid=0'
    df = load_data_from_spreadsheet(spreadsheet_url)

    # Streamlitアプリの表示
    st.title('タイムセール不動産')

    # タグの選択リストを作成
    LOCATION = ["新宿駅","代々木駅","原宿駅", ...]  # 省略

    # サイドバーに最寄り駅のマルチ選択リストを表示
    selected_locations = st.sidebar.multiselect("最寄り駅を選択してください", LOCATION)
    selected_range = st.sidebar.slider("賃料（管理費込）", min_value=10, max_value=50, value=(20,40))
    selected_plan = st.sidebar.multiselect("希望する間取りを選んでください", PLAN)
    selected_size = st.sidebar.slider("部屋の広さを選択してください", min_value=20, max_value=100, value=(40,80))
    selected_wark = st.sidebar.slider("駅徒歩の距離を選択してください", min_value=1, max_value=20, value=(5,15))
    selected_age = st.sidebar.slider("築年の範囲を選択してください", min_value=0, max_value=40, value=(0,10))

    # 「検索する」ボタン
    search_button_clicked = st.sidebar.button("検索する")

    # ボタンが押された場合の処理
    if search_button_clicked:
        # 選択された条件に基づいてデータを絞り込む
        filtered_data = df[
            (df['最寄り駅'].str.contains('|'.join(selected_locations))) &
            (df['合計金額'].astype(int) >= selected_range[0]) &
            (df['合計金額'].astype(int) <= selected_range[1]) &
            (df['間取り'].isin(selected_plan)) &
            (df['面積'].astype(int) >= selected_size[0]) &
            (df['面積'].astype(int) <= selected_size[1]) &
            (df['駅徒歩'].astype(int) >= selected_wark[0]) &
            (df['駅徒歩'].astype(int) <= selected_wark[1]) &
            (df['築年情報'].astype(int) >= selected_age[0]) &
            (df['築年情報'].astype(int) <= selected_age[1])
        ]

        # 絞り込まれたデータを表示
        st.write('絞り込まれたデータ:')
        st.write(filtered_data)

# Streamlitアプリを実行
if __name__ == "__main__":
    main()