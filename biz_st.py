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

'#### :orange[이미지: st. image()]'
st.image("./data/python.png", caption="파이썬 로고", width=500)

'#### :orange[오디오: st.audio()]'
st.audio("./data/After_You-mp3", format="audio/mpeg", loop=True)

'#### :orange[동영상: st.video()]' 
#'rb' : 바이너리 모드로 파일 열기
video_file = open("./data/stars.mp4","rb")
video_bytes = video_file.read()

st. video(video_bytes)

st.divider() # 구분선

'#### :orange[정보: st.info()]'
st.info(
    icon="☀️",
    body='''
    **: sunglasses: 이것은 정보를 제공하는 콜아웃입니다.**
    - :red[빨간색 텍스트]
    - :blue[파란색 텍스트]
    - :green[초록색 텍스트]
    - :orange[주황색 텍스트]
    '''
)
'#### :orange[경고: st.warning()]' 
st. warning('This is a warning message', icon="☁️")

'#### :orange[에러: st.error()]'
st.error('This is an error message', icon="🎶")

'#### :orange[성공: st.success()]'
st. success('This is a success message', icon="❤️ ")

