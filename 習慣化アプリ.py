# =============================================
# 習慣化アプリ - app.py (Google Sheets対応版)
# =============================================
import streamlit as st
import json
from datetime import datetime, date, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import calendar
import matplotlib.font_manager as fm
import gspread
from google.oauth2.service_account import Credentials
 
# =============================================
# 日本語フォント設定
# =============================================
def set_japanese_font():
    japanese_fonts = [
        'Hiragino Sans', 'Hiragino Maru Gothic Pro', 'AppleGothic',
        'Noto Sans CJK JP', 'IPAexGothic', 'MS Gothic',
    ]
    available = [f.name for f in fm.fontManager.ttflist]
    for font in japanese_fonts:
        if font in available:
            plt.rcParams['font.family'] = font
            return font
    plt.rcParams['font.family'] = 'DejaVu Sans'
    return 'DejaVu Sans'
 
FONT = set_japanese_font()
 
# =============================================
# Google Sheets 接続
# =============================================
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
 
@st.cache_resource
def get_sheet():
    """
    Google Sheetsに接続してシートオブジェクトを返す。
    @st.cache_resource で一度だけ接続し、使い回す。
    """
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    # "habit-tracker"という名前のスプレッドシートを開く
    spreadsheet = client.open("habit-tracker")
    # "data"というシートを使う（なければ作成）
    try:
        sheet = spreadsheet.worksheet("data")
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title="data", rows=10, cols=2)
        # 初期データを書き込む
        sheet.update("A1", "key")
        sheet.update("B1", "value")
    return sheet
 
# =============================================
# データの読み込み・保存（Google Sheets版）
# =============================================
def load_data():
    """
    Google Sheetsからデータを読み込む。
    シートのA列がキー、B列が値（JSON文字列）になっている。
    """
    try:
        sheet = get_sheet()
        records = sheet.get_all_records()
        for row in records:
            if row["key"] == "habit_data":
                return json.loads(row["value"])
    except Exception as e:
        st.warning(f"データ読み込みエラー: {e}")
 
    # データがなければ初期値を返す
    return {
        "habits": [],
        "records": {},
        "habit_start_dates": {},
        "weekly_goals": {},
        "weekly_records": {}
    }
 
def save_data(data):
    """
    データをGoogle Sheetsに保存する。
    全データをJSON文字列に変換してB列に保存。
    """
    try:
        sheet = get_sheet()
        json_str = json.dumps(data, ensure_ascii=False)
        # A列を検索してhabit_dataの行を探す
        try:
            cell = sheet.find("habit_data")
            sheet.update_cell(cell.row, 2, json_str)
        except gspread.exceptions.CellNotFound:
            # なければ新しく追加
            sheet.append_row(["habit_data", json_str])
    except Exception as e:
        st.error(f"データ保存エラー: {e}")
 
# =============================================
# パスワード認証
# =============================================
#def check_password():
 # if not st.session_state.authenticated:
  #      st.title("🔒 ログイン")
   #     password = st.text_input("パスワードを入力", type="password")
    #    if st.button("ログイン"):
     #       if password == st.secrets.get("app_password", "password"):
      #          st.session_state.authenticated = True
       #         st.rerun()
        #    else:
         #       st.error("パスワードが違います")
        #st.stop()
 
# =============================================
# 週の月曜日を取得するヘルパー関数
# =============================================
def get_week_monday(d):
    return d - timedelta(days=d.weekday())
 
# =============================================
# カレンダー描画関数
# =============================================
def draw_calendar(year, month, habit_name, records, habit_start_dates):
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_xlim(0, 7)
    num_days = calendar.monthrange(year, month)[1]
    first_weekday = calendar.monthrange(year, month)[0]
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    num_weeks = ((num_days + first_weekday - 1) // 7) + 1
    ax.set_ylim(0, num_weeks + 1)
    ax.axis("off")
    if FONT != 'DejaVu Sans':
        ax.set_title(f"{year}年{month}月  [{habit_name}]", fontsize=14, pad=10)
    else:
        ax.set_title(f"{year}/{month:02d}  [{habit_name}]", fontsize=14, pad=10)
    for i, wd in enumerate(weekdays):
        ax.text(i + 0.5, num_weeks + 0.5, wd, ha="center", va="center",
                fontsize=9, fontweight="bold", color="#555")
    start_date_str = habit_start_dates.get(habit_name, "2000-01-01")
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    day = 1
    for week in range(num_weeks):
        for weekday in range(7):
            if week == 0 and weekday < first_weekday:
                continue
            if day > num_days:
                break
            date_str = f"{year}-{month:02d}-{day:02d}"
            this_date = date(year, month, day)
            today = date.today()
            day_records = records.get(date_str, {})
            status = day_records.get(habit_name)
            if this_date < start_date:
                color, text_color, display = "#F5F5F5", "#CCC", "-"
            elif this_date > today:
                color, text_color, display = "#F5F5F5", "#CCC", str(day)
            elif status is True:
                color, text_color, display = "#4CAF50", "white", str(day)
            elif status is False:
                color, text_color, display = "#F44336", "white", str(day)
            else:
                color, text_color, display = "#E0E0E0", "#888", str(day)
            edge_color = "#FF9800" if date_str == today.strftime("%Y-%m-%d") else color
            lw = 2.5 if date_str == today.strftime("%Y-%m-%d") else 0.5
            rect = mpatches.FancyBboxPatch(
                (weekday + 0.1, num_weeks - week - 0.9), 0.8, 0.8,
                boxstyle="round,pad=0.05", facecolor=color, edgecolor=edge_color, linewidth=lw
            )
            ax.add_patch(rect)
            ax.text(weekday + 0.5, num_weeks - week - 0.5, display,
                    ha="center", va="center", fontsize=10, color=text_color)
            day += 1
    legend_elements = [
        mpatches.Patch(facecolor="#4CAF50", label="達成" if FONT != 'DejaVu Sans' else "Done"),
        mpatches.Patch(facecolor="#F44336", label="未達成" if FONT != 'DejaVu Sans' else "Missed"),
        mpatches.Patch(facecolor="#E0E0E0", label="未記録" if FONT != 'DejaVu Sans' else "No record"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=8)
    plt.tight_layout()
    return fig
 
# =============================================
# 週間達成率グラフ関数
# =============================================
def draw_weekly_chart(habit_name, records, habit_start_dates):
    today = date.today()
    weekly_data = []
    start_date_str = habit_start_dates.get(habit_name, "2000-01-01")
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    for week_offset in range(7, -1, -1):
        week_start = today - timedelta(days=today.weekday()) - timedelta(weeks=week_offset)
        achieved = 0
        total = 0
        for i in range(7):
            d = week_start + timedelta(days=i)
            if d > today or d < start_date:
                continue
            date_str = d.strftime("%Y-%m-%d")
            day_records = records.get(date_str, {})
            if habit_name in day_records:
                total += 1
                if day_records[habit_name]:
                    achieved += 1
        rate = (achieved / total * 100) if total > 0 else 0
        label = f"{week_start.month}/{week_start.day}"
        weekly_data.append({"week": label, "rate": rate, "total": total})
    df = pd.DataFrame(weekly_data)
    fig, ax = plt.subplots(figsize=(9, 4))
    colors = ["#4CAF50" if r >= 70 else "#FF9800" if r >= 40 else "#F44336" for r in df["rate"]]
    bars = ax.bar(df["week"], df["rate"], color=colors, edgecolor="white", width=0.6)
    for bar, row in zip(bars, weekly_data):
        if row["total"] > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                    f"{row['rate']:.0f}%", ha="center", va="bottom", fontsize=9)
    ax.set_ylim(0, 115)
    if FONT != 'DejaVu Sans':
        ax.set_ylabel("達成率 (%)", fontsize=10)
        ax.set_xlabel("週の開始日 (月曜日)", fontsize=10)
        ax.set_title(f"週間達成率: {habit_name}", fontsize=13)
    else:
        ax.set_ylabel("Rate (%)", fontsize=10)
        ax.set_xlabel("Week start (Mon)", fontsize=10)
        ax.set_title(f"Weekly rate: {habit_name}", fontsize=13)
    ax.axhline(y=70, color="green", linestyle="--", alpha=0.4, linewidth=1)
    ax.set_facecolor("#FAFAFA")
    fig.patch.set_facecolor("#FFFFFF")
    plt.tight_layout()
    return fig
 
# =============================================
# メインアプリ
# =============================================
def main():
    st.set_page_config(page_title="習慣トラッカー", page_icon="✅", layout="centered")
    st.markdown("<style>.stButton>button { width: 100%; }</style>", unsafe_allow_html=True)
 
    check_password()
 
    st.title("✅ 習慣トラッカー")
 
    data = load_data()
    habits = data["habits"]
    records = data["records"]
    if "habit_start_dates" not in data:
        data["habit_start_dates"] = {}
    if "weekly_goals" not in data:
        data["weekly_goals"] = {}
    if "weekly_records" not in data:
        data["weekly_records"] = {}
    habit_start_dates = data["habit_start_dates"]
    weekly_goals = data["weekly_goals"]
 
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 毎日チェック", "🎯 週間目標", "📊 一覧表", "📅 カレンダー", "📈 達成率"
    ])
 
    # --------------------------------------------------
    # タブ1：毎日チェック
    # --------------------------------------------------
    with tab1:
        st.markdown("#### 日付を選択")
        selected_date = st.date_input(
            "チェックする日付", value=date.today(),
            max_value=date.today(), label_visibility="collapsed"
        )
        selected_date_str = selected_date.strftime("%Y-%m-%d")
        if FONT != 'DejaVu Sans':
            st.subheader(f"📅 {selected_date.strftime('%Y年%m月%d日')}")
        else:
            st.subheader(f"📅 {selected_date.strftime('%Y/%m/%d')}")
 
        st.markdown("#### 新しい習慣を追加")
        col1, col2 = st.columns([3, 1])
        with col1:
            new_habit = st.text_input("習慣名を入力", placeholder="例：水を2L飲む、早起きする",
                                      label_visibility="collapsed")
        with col2:
            if st.button("追加", use_container_width=True):
                if new_habit and new_habit not in habits:
                    habits.append(new_habit)
                    habit_start_dates[new_habit] = date.today().strftime("%Y-%m-%d")
                    save_data(data)
                    st.success(f"「{new_habit}」を追加しました！")
                    st.rerun()
                elif new_habit in habits:
                    st.warning("その習慣はすでに登録されています")
 
        st.divider()
 
        if not habits:
            st.info("👆 まずは習慣を追加してみましょう！")
        else:
            st.markdown("#### 達成チェック")
            visible_habits = [
                h for h in habits
                if datetime.strptime(habit_start_dates.get(h, "2000-01-01"), "%Y-%m-%d").date() <= selected_date
            ]
            if not visible_habits:
                st.info("この日付にはまだ習慣がありませんでした")
            else:
                selected_records = records.get(selected_date_str, {})
                for habit in visible_habits:
                    col_check, col_label, col_del = st.columns([1, 5, 1])
                    current = selected_records.get(habit)
                    with col_check:
                        checked = st.checkbox("", value=bool(current),
                                              key=f"check_{habit}_{selected_date_str}")
                    with col_label:
                        st.markdown(f"✅ **{habit}**" if checked else f"⬜ {habit}")
                    with col_del:
                        if st.button("🗑️", key=f"del_{habit}", help="習慣を削除"):
                            habits.remove(habit)
                            habit_start_dates.pop(habit, None)
                            save_data(data)
                            st.rerun()
                    if selected_date_str not in records:
                        records[selected_date_str] = {}
                    records[selected_date_str][habit] = checked
                save_data(data)
                achieved = sum(1 for h in visible_habits if records.get(selected_date_str, {}).get(h))
                st.divider()
                st.metric("達成数", f"{achieved} / {len(visible_habits)}",
                          delta=f"{achieved/len(visible_habits)*100:.0f}%" if visible_habits else "0%")
 
    # --------------------------------------------------
    # タブ2：週間目標
    # --------------------------------------------------
    with tab2:
        st.subheader("🎯 週間目標")
        st.markdown("#### 新しい週間目標を追加")
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            new_weekly_name = st.text_input(
                "目標名", placeholder="例：ジムに行く、読書する",
                label_visibility="collapsed", key="weekly_name_input"
            )
        with col2:
            new_weekly_target = st.number_input(
                "週N回", min_value=1, max_value=7, value=3,
                label_visibility="collapsed", key="weekly_target_input"
            )
        with col3:
            if st.button("追加", use_container_width=True, key="add_weekly"):
                if new_weekly_name and new_weekly_name not in weekly_goals:
                    weekly_goals[new_weekly_name] = {
                        "target": int(new_weekly_target),
                        "start_date": date.today().strftime("%Y-%m-%d")
                    }
                    save_data(data)
                    st.success(f"「{new_weekly_name}」週{new_weekly_target}回目標を追加！")
                    st.rerun()
                elif new_weekly_name in weekly_goals:
                    st.warning("その目標はすでに登録されています")
 
        st.divider()
 
        if not weekly_goals:
            st.info("👆 週間目標を追加してみましょう！")
        else:
            today = date.today()
            this_monday = get_week_monday(today)
            st.markdown("#### 今週の達成状況")
 
            for goal_name, goal_info in list(weekly_goals.items()):
                target = goal_info["target"]
                achieved_this_week = 0
                for i in range(7):
                    d = this_monday + timedelta(days=i)
                    if d > today:
                        break
                    date_str = d.strftime("%Y-%m-%d")
                    if data["weekly_records"].get(date_str, {}).get(goal_name):
                        achieved_this_week += 1
 
                col_name, col_del = st.columns([6, 1])
                with col_name:
                    if achieved_this_week >= target:
                        st.markdown(f"### 🏆 {goal_name}")
                    else:
                        st.markdown(f"### {goal_name}")
                with col_del:
                    if st.button("🗑️", key=f"del_weekly_{goal_name}", help="目標を削除"):
                        del weekly_goals[goal_name]
                        save_data(data)
                        st.rerun()
 
                col_count, col_bar = st.columns([1, 3])
                with col_count:
                    color = "green" if achieved_this_week >= target else "orange"
                    st.markdown(
                        f"<h2 style='color:{color}; margin:0'>{achieved_this_week}<span style='font-size:1rem'> / {target}回</span></h2>",
                        unsafe_allow_html=True
                    )
                with col_bar:
                    progress = min(achieved_this_week / target, 1.0)
                    filled = int(progress * 10)
                    bar = "🟩" * filled + "⬜" * (10 - filled)
                    st.markdown(f"<div style='font-size:1.4rem; margin-top:12px'>{bar}</div>",
                                unsafe_allow_html=True)
 
                st.markdown("今週の達成日：")
                week_days_dates = []
                week_days_labels = []
                for i in range(7):
                    d = this_monday + timedelta(days=i)
                    if d > today:
                        break
                    week_days_labels.append(f"{d.month}/{d.day}({'月火水木金土日'[i]})")
                    week_days_dates.append(d)
 
                check_cols = st.columns(len(week_days_dates))
                for i, (d, label) in enumerate(zip(week_days_dates, week_days_labels)):
                    date_str = d.strftime("%Y-%m-%d")
                    current_val = data["weekly_records"].get(date_str, {}).get(goal_name, False)
                    with check_cols[i]:
                        st.markdown(f"<div style='text-align:center;font-size:0.75rem'>{label}</div>",
                                    unsafe_allow_html=True)
                        new_val = st.checkbox("", value=current_val,
                                              key=f"weekly_{goal_name}_{date_str}")
                        if date_str not in data["weekly_records"]:
                            data["weekly_records"][date_str] = {}
                        data["weekly_records"][date_str][goal_name] = new_val
 
                save_data(data)
                st.divider()
 
            st.markdown("#### 過去8週の達成履歴")
            selected_goal = st.selectbox("目標を選択", list(weekly_goals.keys()), key="history_goal")
            if selected_goal:
                target = weekly_goals[selected_goal]["target"]
                history = []
                for week_offset in range(7, -1, -1):
                    w_monday = today - timedelta(days=today.weekday()) - timedelta(weeks=week_offset)
                    count = 0
                    for i in range(7):
                        d = w_monday + timedelta(days=i)
                        if d > today:
                            break
                        date_str = d.strftime("%Y-%m-%d")
                        if data["weekly_records"].get(date_str, {}).get(selected_goal):
                            count += 1
                    label = f"{w_monday.month}/{w_monday.day}"
                    history.append({"week": label, "count": count, "target": target})
 
                fig, ax = plt.subplots(figsize=(9, 4))
                colors = ["#4CAF50" if h["count"] >= h["target"] else "#FF9800" for h in history]
                weeks = [h["week"] for h in history]
                counts = [h["count"] for h in history]
                bars = ax.bar(weeks, counts, color=colors, edgecolor="white", width=0.6)
                for bar, h in zip(bars, history):
                    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                            f"{h['count']}回", ha="center", va="bottom", fontsize=9)
                ax.axhline(y=target, color="red", linestyle="--", alpha=0.6, linewidth=1.5)
                ax.text(7.4, target + 0.05, f"目標{target}回" if FONT != 'DejaVu Sans' else f"Goal:{target}",
                        color="red", fontsize=8, va="bottom")
                ax.set_ylim(0, max(target + 2, max(counts) + 2) if counts else target + 2)
                if FONT != 'DejaVu Sans':
                    ax.set_ylabel("達成回数", fontsize=10)
                    ax.set_xlabel("週の開始日 (月曜日)", fontsize=10)
                    ax.set_title(f"週間達成回数: {selected_goal}", fontsize=13)
                else:
                    ax.set_ylabel("Count", fontsize=10)
                    ax.set_xlabel("Week start (Mon)", fontsize=10)
                    ax.set_title(f"Weekly count: {selected_goal}", fontsize=13)
                ax.set_facecolor("#FAFAFA")
                fig.patch.set_facecolor("#FFFFFF")
                plt.tight_layout()
                st.pyplot(fig)
                st.markdown("🟩 目標達成　🟧 未達成")
 
    # --------------------------------------------------
    # タブ3：一覧表
    # --------------------------------------------------
    with tab3:
        st.subheader("📊 習慣一覧表")
        if not habits:
            st.info("習慣を追加すると一覧表が表示されます")
        else:
            days_to_show = st.slider("表示する日数", min_value=7, max_value=30, value=14, step=7)
            today = date.today()
            date_list = [today - timedelta(days=i) for i in range(days_to_show - 1, -1, -1)]
            table_data = {}
            for habit in habits:
                start_date_str = habit_start_dates.get(habit, "2000-01-01")
                start_date_obj = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                row = {}
                achieved_count = 0
                total_count = 0
                for d in date_list:
                    date_str = d.strftime("%Y-%m-%d")
                    col_label = f"{d.month}/{d.day}"
                    if d < start_date_obj:
                        row[col_label] = "－"
                    else:
                        status = records.get(date_str, {}).get(habit)
                        if status is True:
                            row[col_label] = "✅"
                            achieved_count += 1
                            total_count += 1
                        elif status is False:
                            row[col_label] = "❌"
                            total_count += 1
                        else:
                            row[col_label] = "⬜"
                            total_count += 1
                rate = f"{achieved_count/total_count*100:.0f}%" if total_count > 0 else "-"
                row["達成率"] = rate
                table_data[habit] = row
            df = pd.DataFrame(table_data).T
            st.dataframe(df, use_container_width=True)
            st.markdown("✅ 達成　❌ 未達成　⬜ 未記録　－ 習慣追加前")
 
    # --------------------------------------------------
    # タブ4：カレンダー
    # --------------------------------------------------
    with tab4:
        st.subheader("📅 カレンダーで振り返る")
        if not habits:
            st.info("習慣を追加するとカレンダーが表示されます")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                selected_habit = st.selectbox("習慣を選択", habits)
            with col2:
                selected_year = st.selectbox("年", list(range(2024, 2027)),
                                             index=list(range(2024, 2027)).index(date.today().year))
            with col3:
                selected_month = st.selectbox("月", list(range(1, 13)),
                                              index=date.today().month - 1)
            fig = draw_calendar(selected_year, selected_month, selected_habit, records, habit_start_dates)
            st.pyplot(fig)
 
    # --------------------------------------------------
    # タブ5：週間達成率
    # --------------------------------------------------
    with tab5:
        st.subheader("📈 週間達成率（過去8週）")
        if not habits:
            st.info("習慣を追加すると達成率グラフが表示されます")
        else:
            selected_habit_chart = st.selectbox("習慣を選択", habits, key="chart_habit")
            fig = draw_weekly_chart(selected_habit_chart, records, habit_start_dates)
            st.pyplot(fig)
            st.markdown("""
            **達成率の目安：**
            🟢 70%以上 → 素晴らしい！  
            🟠 40〜70% → もう少し頑張ろう  
            🔴 40%未満 → 習慣を見直してみよう
            """)
 
if __name__ == "__main__":
    main()
