
import streamlit as st
import openai
import urllib.parse

# OpenAI APIキーの設定（StreamlitのSecretsを使用）
try:
    if "openai_api_key" in st.secrets:
        openai.api_key = st.secrets["openai_api_key"]
    else:
        raise KeyError("OpenAI APIキーが設定されていません。StreamlitのSecretsに追加してください。")
except KeyError as e:
    st.error(f"❌ {e}")
    st.stop()

# 質問リスト（Q1で性別を確認）
questions = [
    {"text": "Q1. あなたの性別を選んでください", "choices": ["男性", "女性"]},
    {"text": "Q2. あなたの顔の印象に近いのは？", "choices": ["丸みがあり、やわらかい印象", "直線的で、シャープな印象", "スッキリと縦のラインが際立つ"]},
    {"text": "Q3. あなたの理想の雰囲気は？", "choices": ["知的で洗練された印象", "柔らかく親しみやすい雰囲気", "独自のスタイルを際立たせたい"]},
    {"text": "Q4. あなたのファッションスタイルは？", "choices": ["シンプルで洗練されたスタイル", "自然体でリラックスしたファッション", "個性的でトレンドを意識"]},
    {"text": "Q5. 眼鏡を主に使うシーンは？", "choices": ["仕事やフォーマルな場面で活躍させたい", "日常の相棒として、自然に取り入れたい", "ファッションのアクセントとして楽しみたい"]},
    {"text": "Q6. 眼鏡に関する悩みやコメントを自由に記入してください（任意）", "choices": None},  # フリーワード入力
]

# `st.session_state` の初期化
st.session_state.setdefault("current_question", 0)
st.session_state.setdefault("answers", [])
st.session_state.setdefault("submitted", False)
st.session_state.setdefault("image_url", None)
st.session_state.setdefault("result", "")

# 診断結果の生成（400文字以内に要約）
def generate_result():
    gender = st.session_state["answers"][0]  # 性別取得
    feedback = st.session_state["answers"][-1] if st.session_state["answers"][-1] else "特に悩みなし"  # フリーワード取得
    answers_text = "\n".join([f"{q['text']} {a}" for q, a in zip(questions[1:-1], st.session_state["answers"][1:-1])])

    prompt = f"""
    あなたはプロのアイウェアデザイナーです。
    ユーザーの回答に基づき、最適な眼鏡を提案してください。
    ユーザーの悩みにも配慮し、ポジティブな提案を含め、400文字以内で回答してください。

    **ユーザー情報**
    性別: {gender}
    ユーザーの回答:
    {answers_text}
    眼鏡に関する悩み:
    {feedback}

    **出力フォーマット**
    -----------------------
    あなたにおすすめの眼鏡は【〇〇】です！
    （ポジティブなメッセージ＋眼鏡の特徴を交えて、400文字以内）
    -----------------------
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": prompt}]
    )

    return response["choices"][0]["message"]["content"], gender

# 画像生成（リアルな写真、白背景、眼鏡のみ表示）
def generate_glasses_image(description, gender):
    image_prompt = f"""
    A high-quality, realistic photograph of a single pair of {description} eyeglasses.
    Designed for a {gender}. 
    The glasses should be the only object in the image, centered, with a clean white background.
    No additional elements like text, labels, decorations, faces, or accessories.
    The image should be sharp, well-lit, and professionally rendered.
    """

    response = openai.Image.create(
        model="dall-e-3",
        prompt=image_prompt,
        n=1,
        size="1024x1024"
    )

    return response["data"][0]["url"]

# タイトル表示
st.title("👓 眼鏡デザイン診断")
st.write("あなたにぴったりの眼鏡デザインを診断します！")

# 質問の表示
if st.session_state["current_question"] < len(questions):
    q = questions[st.session_state["current_question"]]
    st.subheader(q["text"])

    if q["choices"]:
        for choice in q["choices"]:
            if st.button(choice):
                st.session_state["answers"].append(choice)
                st.session_state["current_question"] += 1

                if st.session_state["current_question"] == len(questions):
                    st.session_state["submitted"] = True

                st.experimental_rerun()
    else:
        feedback = st.text_area("自由に記入してください（任意）")
        if st.button("次へ"):
            st.session_state["answers"].append(feedback)
            st.session_state["current_question"] += 1
            st.session_state["submitted"] = True
            st.experimental_rerun()

# 診断するボタンの表示
if st.session_state["submitted"] and not st.session_state["result"]:
    st.subheader("🎯 すべての質問に答えました！")
    if st.button("🔍 診断する"):
        result, gender = generate_result()
        st.session_state["result"] = result

        try:
            recommended_glasses = result.split("あなたにおすすめの眼鏡は【")[1].split("】です！")[0]
        except IndexError:
            recommended_glasses = "classic round metal frame glasses"

        st.session_state["image_url"] = generate_glasses_image(recommended_glasses, gender)

        st.experimental_rerun()

# 診断結果の表示（フォントサイズを小さく）
if st.session_state["result"]:
    st.subheader("🔮 診断結果")
    st.markdown(f'<p style="font-size:14px;">{st.session_state["result"]}</p>', unsafe_allow_html=True)

    if st.session_state["image_url"]:
        st.image(st.session_state["image_url"], caption="あなたにおすすめの眼鏡デザイン", use_column_width=True)

    # LINE共有ボタン
    share_text = urllib.parse.quote(f"👓 診断結果: {st.session_state['result']}")
    share_url = f"https://social-plugins.line.me/lineit/share?text={share_text}"
    st.markdown(f"[📲 LINEで友達に共有する]({share_url})", unsafe_allow_html=True)
