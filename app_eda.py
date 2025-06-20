import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Kaggle 데이터셋 출처 및 소개
        st.markdown("""
                ---
                **Population trends 데이터셋**   
                - 설명: 2008년부터 2023년까지 대구, 서울, 제주 등 대한민국 모든 지역에서 인구에 대한 자료
                - 주요 변수:  
                  - `연도`: 해당 연도
                  - `지역`: 대구, 서울 등 대한민국 지역 이름
                  - `인구`: 해당 연도에 해당 지역에 사는 사람 수
                  - `출생아수`: 해당 연도 해당 지역에서 태어난 아이 수
                  - `사망자수`: 해당 연도 해당 지역에서 사망한 사람의 수
                """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 population_trends EDA")
        uploaded_file = st.file_uploader("데이터셋 업로드 (population_trends.csv)", type="csv")
        if not uploaded_file:
            st.info("population_trends.csv 파일을 업로드 해주세요.")
            return
        
        df = pd.read_csv(uploaded_file)

        mask = df['지역'] == '세종'
        df.loc[mask] = df.loc[mask].replace('-', 0)

        # '인구', '출생아수(명)', '사망자수(명)' 열을 숫자 타입으로 변환
        for col in ['인구', '출생아수(명)', '사망자수(명)']:
            #df[col] = df[col].replace('-', 0)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)


        tabs = st.tabs([
            "1. 목적 및 분석 절차",
            "2. 결측치 및 중복 확인",
            "3. 연도별 전체 인구 추이 그래프",
            "4. 지역별 인구 변화량 순위",
            "5. 증감률 상위 지역 및 연도 도출",
            "6. 누적영역그래프 등 적절한 시각화",
        ])

        # 1. 목적 & 분석 절차
        with tabs[0]:
            st.header("🔭 목적 & 분석 절차")
            st.markdown("""
            **목적**: population_trends 데이터셋을 탐색하고,
            연도별 지역 인구 추이를 파악합니다.

            **절차**:
            1. 목적 및 분석 절차
            2. 결측치 및 중복 확인
            3. 연도별 전체 인구 추이 그래프
            4. 지역별 인구 변화량 순위
            5. 증감률 상위 지역 및 연도 도출
            6. 누적영역그래프 등 적절한 시각화
            """)

        # 2. 데이터셋 설명
        with tabs[1]:
            st.header("🔍 결측치 및 중복 확인")
            buffer = io.StringIO()
            df.info(buf=buffer)
            info = buffer.getvalue()
            st.subheader("DataFrame Info")
            st.text(info)

            # 요약 통계 출력
            st.subheader("Descriptive Statistics")
            st.write(df.describe())

                # 데이터 미리보기
            st.subheader("Data Preview")
            st.dataframe(df.head())

        # 3. 연도별 전체 인구 추이 그래프
        with tabs[2]:
            st.header("📥 연도별 전체 인구 추이 그래프")
            nation_df = df[df['지역'] == '전국'].sort_values('연도')

            # Plot historical population trend
            fig, ax = plt.subplots()
            sns.lineplot(data=nation_df, x='연도', y='인구', marker='o', ax=ax)

            # Compute average annual net change from last 3 years
            recent = nation_df.tail(3).copy()
            recent['net_change'] = recent['출생아수(명)'] - recent['사망자수(명)']
            avg_net = recent['net_change'].mean()

            # Project population to 2035
            last_year = nation_df['연도'].iloc[-1]
            last_pop = nation_df['인구'].iloc[-1]
            years = list(nation_df['연도']) + [2035]
            pops = list(nation_df['인구']) + [int(last_pop + avg_net * (2035 - last_year))]
            sns.lineplot(x=years, y=pops, marker='o', linestyle='--', ax=ax)

            # Labels and title in English
            ax.set_title('Population Trend and Projection')
            ax.set_xlabel('Year')
            ax.set_ylabel('Population')
            ax.legend(['Historical', 'Projected'], loc='upper left')

            # Display plot in Streamlit
            st.pyplot(fig)

        # 4. 지역별 인구 변화량 순위
        with tabs[3]:
            st.header("🕒 지역별 인구 변화량 순위")
            st.markdown("`인구` 컬럼에서 각 지역의 값을 비교합니다.")

            years = sorted(df['연도'].unique())
            latest_year = years[-1]
            prev_year = latest_year - 5

            # Filter out nationwide and select by year
            df_latest = df[(df['지역'] != '전국') & (df['연도'] == latest_year)]
            df_prev = df[(df['지역'] != '전국') & (df['연도'] == prev_year)]

            # Merge and compute change and rate
            merged = pd.merge(
                df_latest[['지역', '인구']],
                df_prev[['지역', '인구']],
                on='지역', suffixes=('_latest', '_prev')
            )
            merged['change'] = merged['인구_latest'] - merged['인구_prev']
            merged['change_k'] = merged['change'] / 1000.0
            merged['change_rate'] = merged['change'] / merged['인구_prev'] * 100

            # Translate region names to English
            mapping = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
                '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
                '제주': 'Jeju'
            }
            merged['Region'] = merged['지역'].map(mapping)

            # Sort by absolute change descending
            merged = merged.sort_values('change', ascending=False)

            # Plot absolute change (in thousands)
            fig1, ax1 = plt.subplots()
            sns.barplot(
                x='change_k', y='Region', data=merged,
                ax=ax1, orient='h'
            )
            for i, v in enumerate(merged['change_k']):
                ax1.text(v, i, f"{v:.1f}", va='center')
            ax1.set_title('Population Change by Region (Last 5 Years)')
            ax1.set_xlabel('Population Change (thousands)')
            ax1.set_ylabel('Region')
            st.pyplot(fig1)

            # Plot change rate (% )
            fig2, ax2 = plt.subplots()
            sns.barplot(
                x='change_rate', y='Region', data=merged,
                ax=ax2, orient='h'
            )
            for i, v in enumerate(merged['change_rate']):
                ax2.text(v, i, f"{v:.1f}%", va='center')
            ax2.set_title('Population Change Rate by Region (Last 5 Years)')
            ax2.set_xlabel('Population Change Rate (%)')
            ax2.set_ylabel('Region')
            st.pyplot(fig2)

            # Explanation below the charts
            st.markdown("""
        **분석 결과**
        - 상위 지역은 지난 5년간 절대 인구 증가량이 가장 큰 지역을 나타냅니다.
        - 변화율이 높은 지역일수록 초기 인구 대비 성장 속도가 빠릅니다.
        - 예를 들어, Gyeonggi는 절대 증가량이 가장 크며, Sejong은 변화율 측면에서 가장 높은 성장률을 보였습니다.
        """)

        # 5. 증감률 상위 지역 및 연도 도출
        with tabs[4]:
            st.header("📈 증감률 상위 지역 및 연도 도출")
            # by 근무일 여부
            st.subheader("증가: 파랑 계열, 감소: 빨강 계열")
            
            # Compute yearly diff for each region, excluding '전국'
            df_region = df[df['지역'] != '전국'].sort_values(['지역', '연도']).copy()
            df_region['diff'] = df_region.groupby('지역')['인구'].diff()
            df_region = df_region.dropna(subset=['diff'])

            # Select top 100 increases by diff
            top100 = df_region.sort_values('diff', ascending=False).head(100)

            # Determine symmetric color scale
            max_abs = top100['diff'].abs().max()

            # Style table: format numbers with commas and apply diverging colorbar
            styled = top100[['연도', '지역', '인구', 'diff']].style.format({
                '인구': '{:,.0f}',
                'diff': '{:,.0f}'
            }).background_gradient(
                cmap='bwr', subset=['diff'],
                vmin=-max_abs, vmax=max_abs
            )

            st.subheader("Top 100 Yearly Changes")
            st.dataframe(styled)

        # 6. 누적영역그래프 등 적절한 시각화
        with tabs[5]:
            st.header("🔗 누적영역그래프 등 적절한 시각화")

            # --- Stacked Area Chart by Region Over Time ---
            # Map Korean region names to English
            mapping = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
                '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
                '제주': 'Jeju', '전국': 'Nationwide'
            }
            df['Region'] = df['지역'].map(mapping)
            # Create pivot table
            pivot = df.pivot(index='Region', columns='연도', values='인구').fillna(0)
            years = pivot.columns.tolist()
            data = pivot.values

            # Plot stacked area
            fig, ax = plt.subplots(figsize=(10, 6))
            colors = sns.color_palette('tab20', n_colors=len(pivot))
            ax.stackplot(years, data, labels=pivot.index, colors=colors)
            ax.set_title('Population by Region Over Time')
            ax.set_xlabel('Year')
            ax.set_ylabel('Population')
            ax.legend(loc='upper left', bbox_to_anchor=(1.05, 1))
            plt.tight_layout()
            st.pyplot(fig)

            
            

# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()