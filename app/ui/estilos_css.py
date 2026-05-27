import streamlit as st

def aplicar_estilos_css():
    """Aplica estilos CSS personalizados unificados para toda a aplicação"""
    st.markdown(
        """
        <!-- Carregar fontes -->
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined" rel="stylesheet">

        <style>
            /* Texto global em Inter */
            body, div, p, label, h1, h2, h3, h4, h5, h6 {
                font-family: 'Inter', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif !important;
            }

            /* Ícones garantidos em Material Symbols */
            .material-symbols-outlined,
            [class*="arrow"],
            [class*="icon"],
            [role="button"]::before {
                font-family: 'Material Symbols Outlined' !important;
                font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 48;
            }

            /* Container principal */
            .main .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
                max-width: 1200px;
            }

            /* Header principal com animação */
            .main-header {
                background: linear-gradient(135deg, #ffffff, #f8f9fa);
                padding: 2rem;
                border-radius: 20px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
                text-align: center;
                margin-bottom: 2rem;
                border: 1px solid rgba(255, 255, 255, 0.2);
                backdrop-filter: blur(10px);
            }
            
            .main-header h1 {
                background: linear-gradient(135deg, #495057, #6c757d);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-size: 3rem !important;
                font-weight: 700;
                margin: 0;
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
            }
            
            .main-header h2 {
                background: linear-gradient(135deg, #495057, #6c757d);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-size: 2.5rem !important;
                font-weight: 700;
                margin: 0;
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
            }
            
            .main-header p {
                color: #6c757d;
                font-size: 1.2rem;
                margin-top: 0.5rem;
                font-weight: 400;
            }

            /* Cards modernos */
            .modern-card {
                background: linear-gradient(135deg, #ffffff, #f8f9fa);
                padding: 2rem;
                border-radius: 20px;
                box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
                margin-bottom: 2rem;
                border: 1px solid rgba(255, 255, 255, 0.2);
                backdrop-filter: blur(10px);
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }
            
            .modern-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, #667eea, #764ba2);
            }
            
            .modern-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
            }

            /* Upload area estilizada */
            .upload-area {
                border: 3px dashed #6c757d;
                border-radius: 15px;
                padding: 3rem;
                text-align: center;
                background: linear-gradient(135deg, rgba(108, 117, 125, 0.05), rgba(173, 181, 189, 0.05));
                transition: all 0.3s ease;
                margin: 2rem 0;
            }
            
            .upload-area:hover {
                border-color: #495057;
                background: linear-gradient(135deg, rgba(108, 117, 125, 0.1), rgba(173, 181, 189, 0.1));
                transform: scale(1.02);
            }

            /* Formulários de login estilizados */
            .login-card {
                background: linear-gradient(135deg, #ffffff, #f8f9fa);
                padding: 3rem;
                border-radius: 25px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                margin: 2rem auto;
                max-width: 450px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                backdrop-filter: blur(10px);
                position: relative;
                overflow: hidden;
            }

            .login-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 5px;
                background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
            }

            /* Botões modernos */
            .stButton > button, .stDownloadButton > button {
                background: linear-gradient(135deg, #68707A, #495057) !important;
                color: white !important;
                border: none !important;
                border-radius: 12px !important;
                padding: 0.75rem 2rem !important;
                font-weight: 600 !important;
                transition: all 0.3s ease !important;
                box-shadow: none !important;
                font-family: 'Inter', sans-serif !important;
            }
            
            .stButton > button:hover, .stDownloadButton > button:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 8px 25px rgba(108, 117, 125, 0.3) !important;
            }

            /* Botão primário especial */
            button[kind="primary"] {
                background: linear-gradient(135deg, #1F5082, #164066) !important;
                border: none !important;
                border-radius: 12px !important;
                font-weight: 600 !important;
                transition: all 0.3s ease !important;
            }

            button[kind="primary"]:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 8px 25px rgba(31, 80, 130, 0.3) !important;
            }

            /* Botões dentro de formulários */
            .stForm button[kind="primary"] {
                background: linear-gradient(135deg, #1F5082, #164066) !important;
                color: white !important;
                border: none !important;
                border-radius: 12px !important;
                font-weight: 600 !important;
                transition: all 0.3s ease !important;
            }

            .stForm button[kind="primary"]:hover {
                background: linear-gradient(135deg, #164066, #0f2d4a) !important;
                transform: translateY(-2px) !important;
                box-shadow: 0 8px 25px rgba(31, 80, 130, 0.3) !important;
            }

            /* Botões de submit em formulários */
            .stForm .stFormSubmitButton > button {
                background: linear-gradient(135deg, #1F5082, #164066) !important;
                color: white !important;
                border: none !important;
                border-radius: 12px !important;
                font-weight: 600 !important;
                transition: all 0.3s ease !important;
            }

            .stForm .stFormSubmitButton > button:hover {
                background: linear-gradient(135deg, #164066, #0f2d4a) !important;
                transform: translateY(-2px) !important;
                box-shadow: 0 8px 25px rgba(31, 80, 130, 0.3) !important;
            }

            /* Seletor mais específico para garantir que funcione */
            div[data-testid="stForm"] button[kind="primary"] {
                background: linear-gradient(135deg, #1F5082, #164066) !important;
            }

            /* Inputs estilizados */
            .stTextInput > div > div > input {
                border-radius: 12px !important;
                border: 2px solid #e9ecef !important;
                transition: all 0.3s ease !important;
                font-family: 'Inter', sans-serif !important;
                padding: 12px 16px !important;
            }

            .stTextInput > div > div > input:focus {
                border-color: #6c757d !important;
                box-shadow: 0 0 0 3px rgba(108, 117, 125, 0.1) !important;
            }

            /* Selectbox estilizado */
            .stSelectbox > div > div > div {
                border-radius: 12px !important;
                border: 2px solid #e9ecef !important;
                font-family: 'Inter', sans-serif !important;
            }

            /* Checkbox estilizado */
            .stCheckbox {
                display: flex !important;
                align-items: center !important;
                margin-top: 1.5rem !important;
            }

            .stCheckbox > label {
                display: flex !important;
                align-items: center !important;
                font-weight: 500 !important;
                color: #495057 !important;
                font-family: 'Inter', sans-serif !important;
                margin: 0 !important;
            }

            .stCheckbox > label > div[data-testid="stCheckbox"] {
                margin-right: 0.5rem !important;
                margin-top: 0 !important;
                display: flex !important;
                align-items: center !important;
            }

            .stCheckbox > label > div[data-testid="stCheckbox"] > div {
                background-color: #f8f9fa !important;
                border: 2px solid #6c757d !important;
                border-radius: 8px !important;
                width: 20px !important;
                height: 20px !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
            }

            .stCheckbox > label > div[data-testid="stCheckbox"] > div[data-checkstate="true"] {
                background-color: #6c757d !important;
                border-color: #495057 !important;
            }

            /* Para checkboxes dentro de formulários */
            .stForm .stCheckbox {
                margin-top: 1rem !important;
                margin-bottom: 0.5rem !important;
            }

            /* Métricas */
            .metric-card {
                background: linear-gradient(135deg, #6c757d, #495057);
                color: white;
                padding: 1.5rem;
                border-radius: 15px;
                text-align: center;
                box-shadow: 0 8px 25px rgba(108, 117, 125, 0.3);
                margin: 1rem 0;
            }
            
            .metric-value {
                font-size: 2.5rem;
                font-weight: 700;
                margin: 0;
            }
            
            .metric-label {
                font-size: 0.9rem;
                opacity: 0.9;
                margin-top: 0.5rem;
            }

            /* Alertas estilizados */
            .stAlert {
                border-radius: 12px !important;
                border: none !important;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
                font-family: 'Inter', sans-serif !important;
            }

            /* Success/Error messages styling */
            .stSuccess {
                background: linear-gradient(135deg, rgba(40, 167, 69, 0.1), rgba(40, 167, 69, 0.05)) !important;
                border-left: 4px solid #28a745 !important;
            }

            .stError {
                background: linear-gradient(135deg, rgba(220, 53, 69, 0.1), rgba(220, 53, 69, 0.05)) !important;
                border-left: 4px solid #dc3545 !important;
            }

            .stWarning {
                background: linear-gradient(135deg, rgba(255, 193, 7, 0.1), rgba(255, 193, 7, 0.05)) !important;
                border-left: 4px solid #ffc107 !important;
            }

            /* Info box para instruções */
            .stAlert[data-baseweb="notification"][kind="info"] {
                background: linear-gradient(135deg, rgba(23, 162, 184, 0.1), rgba(23, 162, 184, 0.05)) !important;
                border-left: 4px solid #17a2b8 !important;
                border-radius: 12px !important;
            }

            /* Sidebar estilizada - cinza escuro gradiente */
            .css-1d391kg {
                background: linear-gradient(135deg, #343a40, #495057) !important;
            }

            /* Sidebar container alternativo (dependendo da versão do Streamlit) */
            section[data-testid="stSidebar"] {
                background: linear-gradient(135deg, #343a40, #495057) !important;
            }

            /* Sidebar content */
            .css-1d391kg .css-1v0mbdj {
                background: transparent !important;
            }

            /* Forçar visibilidade de todos os textos na sidebar */
            .stSidebar .stMarkdown p,
            .stSidebar .stCaption,
            .stSidebar div[data-testid="stMarkdownContainer"] p {
                color: #ffffff !important;
                opacity: 1 !important;
            }

            /* Caption específico (tempo de expiração) */
            .stSidebar .stCaption {
                color: #ced4da !important;
                opacity: 1 !important;
            }

            /* Remover qualquer transparência dos captions */
            .stSidebar .stCaption,
            .stSidebar [data-testid="stCaptionContainer"],
            .stSidebar [data-testid="stCaptionContainer"] p,
            .stSidebar .element-container .stCaption {
                color: #ffffff !important;
                opacity: 1 !important;
                background: none !important;
                filter: none !important;
            }

            /* Divider branco na sidebar */
            .stSidebar hr {
                border: none !important;
                height: 1px !important;
                background-color: rgba(255, 255, 255, 0.3) !important;
                margin: 1rem 0 !important;
            }

            /* Sidebar buttons */
            .stSidebar .stButton > button {
                width: 100% !important;
                margin-bottom: 0.5rem !important;
                text-align: left !important;
                justify-content: flex-start !important;
                background: transparent !important;
                color: #ffffff !important;
                border: 1px solid rgba(255, 255, 255, 0.2) !important;
                padding-left: 1rem !important;
                font-weight: 500 !important;
                font-size: 0.8rem !important; 
            }

            .stSidebar .stButton > button:hover {
                background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05)) !important;
                color: #ffffff !important;
                transform: translateX(5px) !important;
                border-color: rgba(255, 255, 255, 0.3) !important;
            }

            /* Botão de logout com destaque */
            .stSidebar .stButton > button[kind="primary"] {
                background: linear-gradient(135deg, #1F5082, #164066) !important;
                color: #ffffff !important;
                border: none !important;
            }

            .stSidebar .stButton > button[kind="primary"]:hover {
                background: linear-gradient(135deg, #c82333, #a71e2a) !important;
                transform: translateX(5px) !important;
            }

            /* Forçar alinhamento à esquerda em todos os botões da sidebar */
            .stSidebar button div {
                text-align: left !important;
                justify-content: flex-start !important;
                width: 100% !important;
            }

            /* Dataframe estilizado */
            .stDataFrame {
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            }

            /* Tabs modernos */
            .stTabs [data-baseweb="tab-list"] {
                gap: 1rem;
                background: rgba(255, 255, 255, 0.1);
                padding: 0.5rem;
                border-radius: 12px;
                backdrop-filter: blur(10px);
            }
            
            .stTabs [data-baseweb="tab"] {
                background: transparent !important;
                color: #6c757d !important;
                font-weight: 500 !important;
                border-radius: 8px !important;
                padding: 0.75rem 1.5rem !important;
                transition: all 0.3s ease !important;
            }
            
            .stTabs [data-baseweb="tab"][aria-selected="true"] {
                background: linear-gradient(135deg, #68707A, #495057) !important;
                color: white !important;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3) !important;
            }
            
            .stTabs [data-baseweb="tab-highlight"] {
                display: none !important;
            }

            /* Caixa padrão para imagem, tabela e botões */
            .stImage, .stDataFrame, .stDownloadButton {
                border-radius: 12px;
                background: #ffffff;
                box-shadow: none !important;
                padding: 10px;
                margin-bottom: 15px;
            }

            /* Imagem em caixa com altura fixa + scroll */
            .stImage {
                height: 700px;
                overflow-y: auto;
            }

            /* Dataframe em caixa com altura fixa + scroll */ 
            .stDataFrame { 
                height: 700px; 
                overflow-y: auto; 
            }

            /* Botão estilizado em caixa */
            .stDownloadButton {
                text-align: center;
                padding: 12px;
                background: linear-gradient(135deg, #343a40, #495057);
                box-shadow: none !important;
            }
            .stDownloadButton > button {
                background: transparent !important;
                color: white !important;
                font-weight: 600 !important;
            }

            /* Estilo para data_editor */
            .stDataEditor {
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            }

            /* Destaque para células editáveis */
            .stDataEditor [data-testid="stDataFrameResizeHandle"] {
                background-color: #f8f9fa;
            }

            /* Form containers */
            .stForm {
                background: transparent !important;
                border: none !important;
                padding: 0 !important;
            }

            /* Progress bars */
            .stProgress > div > div > div {
                background: linear-gradient(90deg, #667eea, #764ba2) !important;
            }

            /* Animações */
            @keyframes fadeInUp {
                from {
                    opacity: 0;
                    transform: translateY(30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            .fade-in-up {
                animation: fadeInUp 0.6s ease-out;
            }

            /* Responsividade */
            @media (max-width: 768px) {
                .main-header h1 {
                    font-size: 2rem !important;
                }
                
                .modern-card, .login-card {
                    padding: 1.5rem;
                    margin: 1rem;
                }
                
                .upload-area {
                    padding: 2rem;
                }
            }

        </style>
        """,
        unsafe_allow_html=True
    )