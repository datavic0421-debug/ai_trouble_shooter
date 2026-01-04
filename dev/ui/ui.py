import streamlit as st
import requests
import socket  # [추가] 네트워크 환경 체크용

def get_api_base_url():
    try:
        # 'api'라는 이름으로 호스트 해석이 가능한지 확인 (도커 네트워크 환경)
        socket.gethostbyname('api')
        return "http://api:8000"
    except socket.gaierror:
        # 해석이 안되면 로컬 환경임
        return "http://localhost:8000"

API_BASE_URL = get_api_base_url()

st.set_page_config(page_title="🔍 AI Trouble Shooter", layout="wide")

st.markdown("## 🔍 AI Trouble Shooter — Code Analyzer")
st.markdown("---")

with st.sidebar:
    st.title("⚙️ 설정")
    level = st.selectbox("사용자 레벨", ["주니어", "시니어"], index=0)

st.markdown("##### 혼자 해결하기 막막한 에러가 있나요? 여기 로그나 코드를 남겨주시면 최적의 해결 방안을 제안해드릴게요!")
col_log, col_code = st.columns(2)
with col_log:
    input_log = st.text_area("🐞 로그 입력", height=250)
with col_code:
    input_code = st.text_area("💡 코드 입력", height=250)

_, center_btn, _ = st.columns([4, 2, 4])
with center_btn:
    analyze_clicked = st.button("🔍 분석하기", use_container_width=True)

# 결과를 저장하기 위한 세션 상태 초기화
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if analyze_clicked:
    if not input_log.strip() and not input_code.strip():
        st.error("❗ 입력을 확인하세요.")
    else:
        with st.spinner("분석 중…"):
            persona_val = "senior" if level == "시니어" else "junior"
            mode = "log_code" if input_log and input_code else ("code" if input_code else "log")
            
            payload = {
                "persona": persona_val,
                "input_mode": mode,
                "error_log": input_log, "code": input_code
            }
            
            try:
                res = requests.post(f"{API_BASE_URL}/analyze/log", json=payload)
                if res.status_code == 200:
                    st.session_state.analysis_result = res.json()
                    st.session_state.last_inputs = payload # 저장 시 사용하기 위해 보관
                else:
                    st.error("분석 실패:정확한 로그나 코드를 입력해주세요!")
            except Exception as e:
                st.error(f"연결 오류: {e}")

# 결과 표시 및 저장 버튼
if st.session_state.analysis_result:
    result = st.session_state.analysis_result
    st.success(f"🎯 {level} 모드 분석 완료!")
    
    # 특정 문구("가이드 생성 완료") 
    p_text = result.get('prevention', "").strip()
    
    # "없습니다"가 포함되어 있거나, "가이드 생성 완료"와 일치하면 숨김 처리(False)
    # 두 조건을 모두 검사하여 더 확실하게 숨깁니다.
    is_prevention_valid = (
        p_text 
        and "없습니다" not in p_text 
        and p_text != "가이드 생성 완료"
    )
    
    # 유효한 예방 가이드가 있을 때만 3개 컬럼, 없으면 2개 컬럼 생성
    if is_prevention_valid:
        cols = st.columns(3)
    else:
        cols = st.columns(2)

    with cols[0]:
        st.info(f"### 🔴 원인\n{result.get('cause')}")
    with cols[1]:
        st.success(f"### 🔵 해결\n{result.get('solution')}")
    
    # 예방 가이드가 유효할 때만 세 번째 컬럼 표시
    if is_prevention_valid:
        with cols[2]:
            st.warning(f"### 🟢 재발 방지\n{p_text}")
    
    st.markdown("---")
    st.markdown("#### 💡 이 답변이 유용했나요?")
    
    if st.button("💾 이 분석 결과를 지식 베이스에 저장하기", use_container_width=True):
        save_payload = {
            "persona": st.session_state.last_inputs["persona"],
            "error_log": st.session_state.last_inputs["error_log"],
            "code": st.session_state.last_inputs["code"],
            "cause": result["cause"],
            "solution": result["solution"]
        }
        try:
            save_res = requests.post(f"{API_BASE_URL}/save/result", json=save_payload)
            if save_res.status_code == 200:
                st.balloons()
                st.success("✅ 성공적으로 저장되었습니다!")
            else:
                st.error("저장 중 오류 발생")
        except Exception as e:
            st.error(f"저장 오류: {e}")