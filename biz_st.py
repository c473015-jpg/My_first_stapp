import streamlit as st # streamlit 라이브러리 임포트

# 타이틀 텍스트 출력
st.title('첫번째 웹 이름 만들기 ☁️')

"## 이건 부제목"

"""
# 비즈니스 모델 분석

[네이버](https://www.naver.com)

[홍익대학교](https://www.hongik.ac.kr/kr/index.do)

이것이 일반 본문 ""이것이 굴은 글씨"" "이것이 기울임 글씨" ~~이것이 

red[빨간 글씨]: blue[파란 글씨]: green[초록 글씨]

"""
import streamlit as st

print("코드블록")

st.caption('캡션(작고 흐린 글씨로 표현) : st.caption()')

with st.echo():
 # 이 블록의 코드와 결과를 출력
 name = 'Soohyun Min'
st.write("Hello, Streamlit", name)

st.latex("\int_a^b f(x)dx")
"$$\int_a^b f(x)dx$$"