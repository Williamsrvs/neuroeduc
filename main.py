from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify,make_response
import json
import os
from datetime import datetime
from flask_mysqldb import MySQL
import pymysql.cursors
import MySQLdb.cursors
from MySQLdb.cursors import DictCursor
from weasyprint import HTML
from io import BytesIO
import pandas as pd
import xlsxwriter
import openpyxl
from flask import send_file
from xhtml2pdf import pisa  # exemplo para converter HTML para PDF
import io


app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'uma_chave_de_dev_aleatoria')

#Configuração MySQL
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', 'Q1k2v1y5@')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'db_funcae')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'  # Importante

mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    # Processa POST de login
    email = request.form['email']
    senha = request.form['senha']

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, senha, tipo_acesso FROM tbl_cad_usuarioslogin WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()

    if user:
        # Verifica a senha (texto puro)
        if user['senha'] == senha:
            session['email'] = email
            session['tipo_acesso'] = user['tipo_acesso']
            flash('Login bem-sucedido!', 'success')
            if user['tipo_acesso'] == 'Master':
                return redirect(url_for('home'))
            else:
                flash('Acesso restrito a Administradores.', 'danger')
                return redirect(url_for('login'))
        else:
            flash('Senha incorreta.', 'danger')
    else:
        flash('Usuário não encontrado.', 'danger')
        
    return redirect(url_for('login'))


@app.route('/home')
def home():
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT COUNT(DISTINCT nome_aluno) AS total_alunos
            FROM tbl_cad_alunos
        """)

        total_alunos = cur.fetchone()['total_alunos']
        cur.close()
        print(f"Total de alunos encontrados: {total_alunos}")  # Debug

    except Exception as e:
        print(f"Erro ao buscar alunos: {e}")
        total_alunos = 0

    return render_template('home.html', total_alunos=total_alunos)

@app.route('/cad_acesso', methods=['GET', 'POST'])
def cad_acesso():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')   
        data_registro = datetime.now().date()
        nome_usuario = request.form.get('nome_usuario')
        email= request.form.get('email')
        dt_nascimento = request.form.get('dt_nascimento')
        senha = request.form.get('senha')
        tipo_acesso = request.form.get('tipo_acesso')

        try:
            cursor = mysql.connection.cursor()
            cursor.execute("""
                INSERT INTO tbl_cad_usuarioslogin (
                    nome_usuario, email, dt_nascimento, senha, tipo_acesso, data_registro
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (nome_usuario, email, dt_nascimento, senha, tipo_acesso, data_registro))
            mysql.connection.commit()
            flash('Usuário cadastrado com sucesso!', 'success')
        except Exception as e:
            flash(f'Erro ao cadastrar usuário: {str(e)}', 'error')
        finally:
            if cursor:
                cursor.close()
        return redirect(url_for('cad_acesso'))

    return render_template('cad_acesso.html')


@app.route('/cad_aluno', methods=['GET', 'POST'])
def cad_aluno():
    if request.method == 'POST':
        nome_aluno = request.form.get('nome_aluno')
        dt_nascimento = request.form.get('dt_nascimento')
        genero = request.form.get('genero')
        endereco_aluno = request.form.get('endereco_aluno')
        tipo_responsavel = request.form.get('tipo_responsavel')
        nome_pai = request.form.get('nome_pai')
        nome_mae = request.form.get('nome_mae')
        patologia = request.form.get('patologia')
        tipo_educacao = request.form.get('tipo_educacao')
        contato = request.form.get('contato')
        nome_escola = request.form.get('nome_escola')
        turma = request.form.get('turma')
        professor_regente = request.form.get('professor_regente')
        profissional_AEE = request.form.get('profissional_AEE')
        cod_cid = request.form.get('cod_cid')
        equipe_multidisciplinar = request.form.get('equipe_multidisciplinar')
        status_aluno = request.form.get('status_aluno')
        observacoes = request.form.get('observacoes')
        data_registro = datetime.now().date()

        try:
            cursor = mysql.connection.cursor()
            cursor.execute("""
                INSERT INTO tbl_cad_alunos (
                    nome_aluno, data_registro, dt_nascimento, genero, endereco_aluno, tipo_responsavel,
                    nome_pai, nome_mae, patologia, tipo_educacao, contato, nome_escola, turma,
                    professor_regente, profissional_AEE, cod_cid, equipe_multidisciplinar, status_aluno, observacoes
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                nome_aluno, data_registro, dt_nascimento, genero, endereco_aluno, tipo_responsavel,
                nome_pai, nome_mae, patologia, tipo_educacao, contato, nome_escola, turma,
                professor_regente, profissional_AEE, cod_cid, equipe_multidisciplinar, status_aluno, observacoes
            ))
            mysql.connection.commit()
            flash('Aluno cadastrado com sucesso!', 'success')
        except Exception as e:
            flash(f'Erro ao cadastrar aluno: {str(e)}', 'error')
        finally:
            if cursor:
                cursor.close()
        return redirect(url_for('cad_aluno'))

    return render_template('cad_aluno.html')


# Buscar aluno por matrícula (AJAX)
@app.route('/buscar_aluno')
def buscar_aluno():
    try:
        # Verificar se a matrícula foi informada
        matricula = request.args.get('matricula_aluno')
        print(f"Matrícula recebida: {matricula}")  # Debug
        
        if not matricula:
            return jsonify({
                'encontrado': False,
                'erro': True,
                'mensagem': 'Matrícula não informada'
            }), 400

        # Verificar conexão com o banco
        if not mysql.connection:
            print("Erro: Conexão com MySQL não estabelecida")
            return jsonify({
                'encontrado': False,
                'erro': True,
                'mensagem': 'Erro de conexão com o banco de dados'
            }), 500

        # Executar consulta
        cursor = mysql.connection.cursor()
        print("Cursor criado com sucesso")  # Debug
        
        query = """
            SELECT 
                id_aluno, matricula_aluno, nome_aluno,
                DATE_FORMAT(dt_nascimento, '%Y-%m-%d') as dt_nascimento,
                genero, endereco_aluno, tipo_responsavel,
                nome_pai, nome_mae, patologia, tipo_educacao,
                contato, nome_escola, turma, professor_regente,
                profissional_AEE, cod_cid, equipe_multidisciplinar,
                status_aluno, observacoes
            FROM tbl_cad_alunos 
            WHERE matricula_aluno = %s
        """
        
        print(f"Executando query: {query}")  # Debug
        print(f"Parâmetro: {matricula}")  # Debug
        
        cursor.execute(query, (matricula,))
        
        # Obter nomes das colunas
        columns = [col[0] for col in cursor.description]
        print(f"Colunas encontradas: {columns}")  # Debug
        
        # Buscar resultado
        aluno = cursor.fetchone()
        print(f"Resultado da consulta: {aluno}")  # Debug
        
        cursor.close()
        print("Cursor fechado")  # Debug
        
        if aluno:
            # Converter para dicionário
            aluno_dict = dict(zip(columns, aluno))
            print(f"Aluno encontrado: {aluno_dict}")  # Debug
            
            return jsonify({
                'encontrado': True,
                'erro': False,
                'aluno': aluno_dict,
                'mensagem': 'Aluno encontrado com sucesso'
            })
        else:
            print("Nenhum aluno encontrado")  # Debug
            return jsonify({
                'encontrado': False,
                'erro': False,
                'mensagem': f'Aluno com matrícula {matricula} não encontrado'
            })

    except mysql.connection.Error as db_error:
        print(f"Erro específico do MySQL: {str(db_error)}")
        print(f"Código do erro: {db_error.args[0] if db_error.args else 'N/A'}")
        
        # Fechar cursor se estiver aberto
        try:
            if 'cursor' in locals():
                cursor.close()
        except:
            pass
            
        return jsonify({
            'encontrado': False,
            'erro': True,
            'mensagem': 'Erro no banco de dados',
            'detalhes': f'MySQL Error: {str(db_error)}'
        }), 500
        
    except AttributeError as attr_error:
        print(f"Erro de atributo (possível problema com mysql.connection): {str(attr_error)}")
        return jsonify({
            'encontrado': False,
            'erro': True,
            'mensagem': 'Erro de configuração do banco de dados',
            'detalhes': f'AttributeError: {str(attr_error)}'
        }), 500
        
    except Exception as e:
        print(f"Erro geral não capturado: {str(e)}")
        print(f"Tipo do erro: {type(e).__name__}")
        import traceback
        print(f"Traceback completo: {traceback.format_exc()}")
        
        # Fechar cursor se estiver aberto
        try:
            if 'cursor' in locals():
                cursor.close()
        except:
            pass
            
        return jsonify({
            'encontrado': False,
            'erro': True,
            'mensagem': 'Erro interno do servidor',
            'detalhes': str(e)
        }), 500


# Rota adicional para testar a conexão com o banco
@app.route('/test_db')
def test_db():
    """Rota para testar a conexão com o banco de dados"""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Conexão com banco OK',
            'test_result': result[0]
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Erro na conexão: {str(e)}'
        }), 500


# Rota para listar todas as tabelas (debug)
@app.route('/list_tables')
def list_tables():
    """Rota para listar tabelas do banco (apenas para debug)"""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'tables': [table[0] for table in tables]
        })
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


# Rota para verificar estrutura da tabela
@app.route('/describe_table')
def describe_table():
    """Rota para verificar estrutura da tabela tbl_cad_alunos"""
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("DESCRIBE tbl_cad_alunos")
        columns = cursor.fetchall()
        cursor.close()
        
        return jsonify({
            'columns': [{'field': col[0], 'type': col[1], 'null': col[2], 'key': col[3]} for col in columns]
        })
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/saiba_mais', methods=['GET'])
def saiba_mais():
    return render_template('saiba_mais.html')

@app.route('/quest_pei', methods=['GET', 'POST'])
def quest_pei():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_aluno, nome_aluno FROM tbl_cad_alunos ORDER BY nome_aluno")
    alunos = cur.fetchall()
    cur.close()

    if request.method == 'POST':
        cur = None  # Inicializa cursor como None
        try:
            aluno_id = request.form.get('aluno_id')
            
            # Validação básica
            if not aluno_id:
                flash('Por favor, selecione um aluno.', 'danger')
                return render_template('quest_pei.html', alunos=alunos)

            cur = mysql.connection.cursor()

            # 1 - Acompanhamento e avaliação
            cur.execute("""
                INSERT INTO tbl_acompanhamento_avaliacao (
                    aluno_id, frequencia_reavaliacao, responsavel_acompanhamento, reunioes
                ) VALUES (%s, %s, %s, %s)
            """, (
                aluno_id,
                request.form.get('frequencia_reavaliacao'),
                request.form.get('responsavel_acompanhamento'),
                request.form.get('reunioes')
            ))

            # 2 - Comportamento e Interação
            cur.execute("""
                INSERT INTO tbl_comportamento_interacao_pei (
                    aluno_id, comunicacao, tipo_linguagem, atividades_grupo, comp_desaf, socializacao
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                aluno_id,
                request.form.get('comunicacao'),
                request.form.get('tipo_linguagem'),
                request.form.get('atividades_grupo'),
                request.form.get('comp_desaf'),
                request.form.get('socializacao')
            ))

            # 3 - Desenvolvimento Geral
            cur.execute("""
                INSERT INTO tbl_desenvolvimento_geral_pei (
                    aluno_id, autonomia, atraso_desenvolvimento, questoes_saude, talentos
                ) VALUES (%s, %s, %s, %s, %s)
            """, (
                aluno_id,
                request.form.get('autonomia'),
                request.form.get('atraso_desenvolvimento'),
                request.form.get('questoes_saude'),
                request.form.get('talentos')
            ))

            # 4 - Estratégia e Adaptações
            cur.execute("""
                INSERT INTO tbl_estrategias_adaptacoes_pei (
                    aluno_id, estrategias, adaptacoes_curriculares, materiais_concretos, avaliacoes
                ) VALUES (%s, %s, %s, %s, %s)
            """, (
                aluno_id,
                request.form.get('estrategias'),
                request.form.get('adaptacoes_curriculares'),
                request.form.get('materiais_concretos'),
                request.form.get('avaliacoes')
            ))

            # 5 - Habilidades Escolares
            cur.execute("""
                INSERT INTO tbl_habilidades_escolares_pei (
                    aluno_id, leitura_escrita, numeros_matematica, interesse_aulas, recursos_aprendizagem, barreiras
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                aluno_id,
                request.form.get('leitura_escrita'),
                request.form.get('numeros_matematica'),
                request.form.get('interesse_aulas'),
                request.form.get('recursos_aprendizagem'),
                request.form.get('barreiras')
            ))

            # 6 - Necessidade de Apoio
            # Tratamento especial para campo múltiplo
            apoios = request.form.getlist('apoios')  # Use getlist para select múltiplo
            apoios_str = ','.join(apoios) if apoios else None
            
            cur.execute("""
                INSERT INTO tbl_necessidades_apoio_pei (
                    aluno_id, apoios, equipamentos
                ) VALUES (%s, %s, %s)
            """, (
                aluno_id,
                apoios_str,
                request.form.get('equipamentos')
            ))

            # 7 - Objetivos PEI
            cur.execute("""
                INSERT INTO tbl_objetivos_pei (
                    aluno_id, objetivo_cognitivo, objetivo_linguagem, objetivo_autonomia, 
                    objetivo_interacao, objetivo_motor, objetivo_comportamento
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                aluno_id,
                request.form.get('objetivo_cognitivo'),
                request.form.get('objetivo_linguagem'),
                request.form.get('objetivo_autonomia'),
                request.form.get('objetivo_interacao'),
                request.form.get('objetivo_motor'),
                request.form.get('objetivo_comportamento')
            ))

            # 8 - Outras Informações
            cur.execute("""
                INSERT INTO tbl_outras_informacoes_pei (
                    aluno_id, historico_escolar, consideracoes_familia, 
                    observacoes_professores, comentarios_equipe
                ) VALUES (%s, %s, %s, %s, %s)
            """, (
                aluno_id,
                request.form.get('historico_escolar'),
                request.form.get('consideracoes_familia'),
                request.form.get('observacoes_professores'),
                request.form.get('comentarios_equipe')
            ))

            # Commit das transações
            mysql.connection.commit()
            cur.close()
            flash('Questionário PEI salvo com sucesso!', 'success')
            return redirect(url_for('quest_pei'))
            
        except Exception as e:
            # Rollback em caso de erro
            mysql.connection.rollback()
            if cur:
                cur.close()
            print(f"Erro detalhado: {str(e)}")  # Para debug
            flash(f'Erro ao salvar: {str(e)}', 'danger')
            return render_template('quest_pei.html', alunos=alunos)

    return render_template('quest_pei.html', alunos=alunos)



@app.route('/gerar_pdf_pei', methods=['GET', 'POST'])
def gerar_pdf_pei():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_aluno, nome_aluno FROM tbl_cad_alunos ORDER BY nome_aluno")
    alunos = cur.fetchall()
    cur.close()

    aluno_selecionado = None

    if request.method == 'POST':
        id_aluno = request.form.get('id_aluno')
        if id_aluno:
            return redirect(url_for('gerar_pdf_pei', id_aluno=id_aluno))
        else:
            flash('Por favor, selecione um aluno.', 'danger')
            return redirect(url_for('gerar_pdf_pei'))

    id_aluno = request.args.get('id_aluno')
    if id_aluno:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM vw_quest_pei WHERE id_aluno = %s", (id_aluno,))
        respostas = cur.fetchone()
        cur.close()

        if not respostas:
            flash('Aluno não encontrado ou sem respostas PEI.', 'danger')
            return redirect(url_for('gerar_pdf_pei'))
        aluno = {
        "id_aluno": respostas.get("id_aluno"),
        "nome_aluno": respostas.get("nome_aluno"),
        "matricula_aluno": respostas.get("matricula_aluno"),
        "dt_nascimento": respostas.get("dt_nascimento")
        }

        html = render_template('relatorio_pdf_pei.html', aluno=aluno, respostas=respostas)
        pdf = BytesIO()
        pisa_status = pisa.CreatePDF(html, dest=pdf)
        if pisa_status.err:
            flash('Erro ao gerar o PDF.', 'danger')
            return redirect(url_for('gerar_pdf_pei'))

        pdf.seek(0)
        nome_aluno = respostas.get("nome_aluno", "Aluno")
        return send_file(
            pdf,
            mimetype='application/pdf',
            download_name=f'Relatorio_PEI_Aluno_{nome_aluno}.pdf',
            as_attachment=False
        )

    return render_template('gerar_pdf_pei.html', alunos=alunos, aluno_selecionado=aluno_selecionado)


@app.route('/pdf_pei', methods=['GET'])
def pdf_pei():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM db_funcae.vw_quest_pei")
    dados = cur.fetchall()
    cur.close()

@app.route('/pei_excel', methods=['GET'])
def pei_excel():
    cur = mysql.connection.cursor()
    cur.execute("""SELECT  
	id_aluno,
    matricula_aluno,
    nome_aluno,
    idade,
    id_desenvolvimento,
    autonomia,
    atraso_desenvolvimento,
    questoes_saude,
    talentos,
    id_habilidade,
    leitura_escrita,
    numeros_matematica,
    interesse_aulas,
    recursos_aprendizagem,
    barreiras,
    id_comportamento,
    comunicacao,
    tipo_linguagem,
    atividades_grupo,
    comp_desaf,
    socializacao,
    id_necessidade,
    apoios,
    equipamentos,
    id_estrategia,
    estrategias,
    adaptacoes_curriculares,
    materiais_concretos,
    avaliacoes,
    id_objetivo,
    objetivo_cognitivo,
    objetivo_linguagem,
    objetivo_autonomia,
    objetivo_interacao,
    objetivo_motor,
    objetivo_comportamento,
    id_informe,
    historico_escolar,
    consideracoes_familia,
    observacoes_professores,
    comentarios_equipe,
    id_acomp_av,
    frequencia_reavaliacao,
    responsavel_acompanhamento,
    reunioes
FROM db_funcae.vw_quest_pei""")
    dados = cur.fetchall()
    cur.close()

    # Se não vier nenhum dado, retorna mensagem simples
    if not dados:
        return "Nenhum dado para exportar.", 404

    # Cria um DataFrame pandas com os dados retornados
    df = pd.DataFrame(dados)

    # Usa BytesIO para criar arquivo Excel na memória
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='PEI')

    output.seek(0)

    # Retorna o arquivo Excel para download
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='relatorio_pei.xlsx'
    )
    

@app.route('/alunos_ativos_excel', methods=['GET'])
def alunos_ativos_excel():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM tbl_cad_alunos WHERE status_aluno = 'Ativo'")
    alunos = cur.fetchall()
    colunas = [desc[0] for desc in cur.description]
    cur.close()

    if not alunos:
        return "Nenhum aluno ativo encontrado.", 404

    df = pd.DataFrame(alunos, columns=colunas)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Alunos Ativos')
    output.seek(0)

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='alunos_ativos.xlsx'
    )



from datetime import datetime

@app.route('/baixa_alunos', methods=['GET'])
def baixa_alunos():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    # Corrigido: buscar todos os alunos, não apenas os da view de baixados
    cur.execute("""
        SELECT id_aluno, matricula_aluno, nome_aluno, dt_nascimento, 
               idade, patologia, status_aluno 
        FROM tbl_cad_alunos 
        ORDER BY nome_aluno
    """)
    alunos = cur.fetchall()
    cur.close()
    return render_template('baixa_alunos.html', alunos=alunos)

@app.route('/baixar_aluno/<int:id_aluno>', methods=['POST'])
def baixar_aluno(id_aluno):
    try:
        motivo = request.form.get('motivo', '')
        observacoes = request.form.get('observacoes', '')
        data_baixa = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cur = mysql.connection.cursor()
        
        # 1. Atualizar status do aluno para "Inativo"
        cur.execute("""
            UPDATE tbl_cad_alunos 
            SET status_aluno = 'Inativo' 
            WHERE id_aluno = %s
        """, (id_aluno,))
        
        # 2. Inserir registro na tabela de baixas (se existir)
        # Se você não tem essa tabela, pode criar ou comentar esta parte
        try:
            cur.execute("""
                INSERT INTO tbl_baixas_alunos 
                (aluno_id, motivo_baixa, observacoes, data_baixa, usuario_baixa) 
                VALUES (%s, %s, %s, %s, %s)
            """, (id_aluno, motivo, observacoes, data_baixa, session.get('user_id', 'Sistema')))
        except Exception as e:
            # Se a tabela não existir, apenas registra no log
            print(f"Aviso: Tabela de baixas não encontrada: {e}")
        
        mysql.connection.commit()
        cur.close()
        
        flash('Aluno dado como baixa com sucesso!', 'success')
        
    except Exception as e:
        mysql.connection.rollback()
        if cur:
            cur.close()
        flash(f'Erro ao dar baixa no aluno: {str(e)}', 'danger')
    
    return redirect(url_for('baixa_alunos'))

@app.route('/reativar_aluno/<int:id_aluno>', methods=['POST'])
def reativar_aluno(id_aluno):
    try:
        cur = mysql.connection.cursor()
        
        # Reativar aluno
        cur.execute("""
            UPDATE tbl_cad_alunos 
            SET status_aluno = 'Ativo' 
            WHERE id_aluno = %s
        """, (id_aluno,))
        
        # Registrar reativação (opcional)
        try:
            cur.execute("""
                INSERT INTO tbl_baixas_alunos 
                (aluno_id, motivo_baixa, observacoes, data_baixa, usuario_baixa) 
                VALUES (%s, %s, %s, %s, %s)
            """, (id_aluno, 'REATIVAÇÃO', 'Aluno reativado no sistema', 
                  datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                  session.get('user_id', 'Sistema')))
        except:
            pass  # Se não tiver tabela de log, ignora
        
        mysql.connection.commit()
        cur.close()
        
        flash('Aluno reativado com sucesso!', 'success')
        
    except Exception as e:
        mysql.connection.rollback()
        if cur:
            cur.close()
        flash(f'Erro ao reativar aluno: {str(e)}', 'danger')
    
    return redirect(url_for('baixa_alunos'))

@app.route('/baixa_lote', methods=['POST'])
def baixa_lote():
    try:
        alunos_ids = request.form.getlist('alunos_ids')
        
        if not alunos_ids:
            flash('Nenhum aluno selecionado!', 'warning')
            return redirect(url_for('baixa_alunos'))
        
        cur = mysql.connection.cursor()
        
        # Baixa em lote
        for aluno_id in alunos_ids:
            cur.execute("""
                UPDATE tbl_cad_alunos 
                SET status_aluno = 'Inativo' 
                WHERE id_aluno = %s AND status_aluno = 'Ativo'
            """, (aluno_id,))
            
            # Log da baixa em lote
            try:
                cur.execute("""
                    INSERT INTO tbl_baixas_alunos 
                    (aluno_id, motivo_baixa, observacoes, data_baixa, usuario_baixa) 
                    VALUES (%s, %s, %s, %s, %s)
                """, (aluno_id, 'BAIXA EM LOTE', 'Baixa realizada em lote', 
                      datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                      session.get('user_id', 'Sistema')))
            except:
                pass
        
        mysql.connection.commit()
        cur.close()
        
        flash(f'{len(alunos_ids)} aluno(s) dado(s) como baixa com sucesso!', 'success')
        
    except Exception as e:
        mysql.connection.rollback()
        if cur:
            cur.close()
        flash(f'Erro na baixa em lote: {str(e)}', 'danger')
    
    return redirect(url_for('baixa_alunos'))

# Rota adicional para criar tabela de log de baixas (opcional)
@app.route('/criar_tabela_baixas')
def criar_tabela_baixas():
    """Rota para criar tabela de log de baixas - use apenas uma vez"""
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tbl_baixas_alunos (
                id_baixa INT AUTO_INCREMENT PRIMARY KEY,
                aluno_id INT NOT NULL,
                motivo_baixa VARCHAR(100),
                observacoes TEXT,
                data_baixa DATETIME,
                usuario_baixa VARCHAR(50),
                FOREIGN KEY (aluno_id) REFERENCES tbl_cad_alunos(id_aluno)
            )
        """)
        mysql.connection.commit()
        cur.close()
        return "Tabela de baixas criada com sucesso!"
    except Exception as e:
        return f"Erro ao criar tabela: {str(e)}"


@app.route('/quest_pedi', methods=['GET', 'POST'])
def quest_pedi():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_aluno, nome_aluno FROM tbl_cad_alunos ORDER BY nome_aluno")
    alunos = cur.fetchall()
    cur.close()

    if request.method == 'POST':
        try:
            aluno_id = request.form.get('aluno_id')

            # CUIDADO PESSOAL
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO tbl_quest_pedi_cuidadopessoal (
                    alimentacao_talher, mastigacao, ingestao_liquidos, cortar_alimentos, recurso_comer,
                    escovacao_dentes, higiene_maos, papel_higienico, enxugase_banho, lembrete_higiene,
                    vestimenta_camisa, vestimenta_calca, autonomia_ziper_amarras, calcados, diferencia_frente_verso,
                    comunicacao_banheiro, autonomia_vaso_sanitario, acidentes_urina_outros, lavar_maos, supervisao_banheiro,
                    observacoes, aluno_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                request.form.get('alimentacao_talher'),
                request.form.get('mastigacao'),
                request.form.get('ingestao_liquidos'),
                request.form.get('cortar_alimentos'),
                request.form.get('recurso_comer'),
                request.form.get('escovacao_dentes'),
                request.form.get('higiene_maos'),
                request.form.get('papel_higienico'),
                request.form.get('enxugase_banho'),
                request.form.get('lembrete_higiene'),
                request.form.get('vestimenta_camisa'),
                request.form.get('vestimenta_calca'),
                request.form.get('autonomia_ziper_amarras'),
                request.form.get('calcados'),
                request.form.get('diferencia_frente_verso'),
                request.form.get('comunicacao_banheiro'),
                request.form.get('autonomia_vaso_sanitario'),
                request.form.get('acidentes_urina_outros'),
                request.form.get('lavar_maos'),
                request.form.get('supervisao_banheiro'),
                request.form.get('observacoes'),
                aluno_id
            ))

            # MOBILIDADE
            cur.execute("""
                INSERT INTO tbl_quest_pedi_mobilidade (
                    senta_sozinho, levanta_cadeira, anda_sozinho, abre_portas, locomocao_escadas, locomocao_terrenos,
                    usa_transporte, empurra_brinquedos, corre_pula, cadeira_rodas, observacoes_mobilidade, aluno_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                request.form.get('senta_sozinho'),
                request.form.get('levanta_cadeira'),
                request.form.get('anda_sozinho'),
                request.form.get('abre_portas'),
                request.form.get('locomocao_escadas'),
                request.form.get('locomocao_terrenos'),
                request.form.get('usa_transporte'),
                request.form.get('empurra_brinquedos'),
                request.form.get('corre_pula'),
                request.form.get('cadeira_rodas'),
                request.form.get('observacoes_mobilidade'),
                aluno_id
            ))

            # FUNÇÃO SOCIAL
            cur.execute("""
                INSERT INTO tbl_quest_pedi_funcaosocial (
                    responde_chamado, contato_visual, imita_acoes, participa_brincadeiras, respeita_turnos,
                    fala_palavras, gestos_sinais, pede_ajuda, compreende_instrucoes, expressa_sentimento,
                    guarda_brinquedo, lembra_atividades, cumpre_combinado, escolhe_roupas, demonstra_interesse,
                    observacoes_fun_social, aluno_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                request.form.get('responde_chamado'),
                request.form.get('contato_visual'),
                request.form.get('imita_acoes'),
                request.form.get('participa_brincadeiras'),
                request.form.get('respeita_turnos'),
                request.form.get('fala_palavras'),
                request.form.get('gestos_sinais'),
                request.form.get('pede_ajuda'),
                request.form.get('compreende_instrucoes'),
                request.form.get('expressa_sentimento'),
                request.form.get('guarda_brinquedo'),
                request.form.get('lembra_atividades'),
                request.form.get('cumpre_combinado'),
                request.form.get('escolhe_roupas'),
                request.form.get('demonstra_interesse'),
                request.form.get('observacoes_fun_social'),
                aluno_id
            ))

            mysql.connection.commit()
            cur.close()
            flash('Questionário PEDI salvo com sucesso!', 'success')
            return redirect(url_for('quest_pedi'))

        except Exception as e:
            mysql.connection.rollback()
            if cur:
                cur.close()
            flash(f'Erro ao salvar: {str(e)}', 'danger')
            return render_template('quest_pedi.html', alunos=alunos)

    return render_template('quest_pedi.html', alunos=alunos)

@app.route('/gerar_pdf_pdi', methods=['GET', 'POST'])
def gerar_pdf_pdi():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_aluno, nome_aluno FROM tbl_cad_alunos ORDER BY nome_aluno")
    alunos = cur.fetchall()
    cur.close()

    if request.method == 'POST':
        id_aluno = request.form.get('id_aluno')
        if id_aluno:
            return redirect(url_for('gerar_pdf_pdi', id_aluno=id_aluno))
        else:
            flash('Por favor, selecione um aluno.', 'danger')
            return redirect(url_for('gerar_pdf_pdi'))

    id_aluno = request.args.get('id_aluno')
    if id_aluno:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM vw_quest_pedi WHERE id_aluno = %s", (id_aluno,))
        respostas = cur.fetchone()
        cur.close()

        if not respostas:
            flash('Aluno não encontrado ou sem respostas PEDI.', 'danger')
            return redirect(url_for('gerar_pdf_pdi'))

        # Passa todas as respostas diretamente para o template
        html = render_template('relatorio_pdf_pedi.html', respostas=respostas)
        pdf = BytesIO()
        pisa_status = pisa.CreatePDF(html, dest=pdf)
        if pisa_status.err:
            flash('Erro ao gerar o PDF.', 'danger')
            return redirect(url_for('gerar_pdf_pdi'))

        pdf.seek(0)
        nome_aluno = respostas.get("nome_aluno", "Aluno")
        return send_file(
            pdf,
            mimetype='application/pdf',
            download_name=f'Relatorio_PEDI_Aluno_{nome_aluno}.pdf',
            as_attachment=False
        )

    return render_template('gerar_pdf_pdi.html', alunos=alunos)

#gerando pdf pedi
@app.route('/pdf_pdi', methods=['GET'])
def pdf_pdi():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM db_funcae.vw_quest_pedi")
    dados = cur.fetchall()
    cur.close()

@app.route('/gerar_excel_pdi', methods=['GET'])
def gerar_excel_pdi():
    cur = mysql.connection.cursor()
    cur.execute("""SELECT  
        id_aluno,
        matricula_aluno,
        nome_aluno,
        idade,
        id_cuid_pessoal,
        alimentacao_talher,
        mastigacao,
        ingestao_liquidos,
        cortar_alimentos,
        recurso_comer,
        escovacao_dentes,
        higiene_maos,
        papel_higienico,
        enxugase_banho,
        lembrete_higiene,
        vestimenta_camisa,
        vestimenta_calca,
        autonomia_ziper_amarras,
        calcados,
        diferencia_frente_verso,
        comunicacao_banheiro,
        autonomia_vaso_sanitario,
        acidentes_urina_outros,
        lavar_maos,
        supervisao_banheiro,
        observacoes,
        id_mobilidade,
        senta_sozinho,
        levanta_cadeira,
        anda_sozinho,
        abre_portas,
        locomocao_escadas,
        locomocao_terrenos,
        usa_transporte,
        empurra_brinquedos,
        corre_pula,
        cadeira_rodas,
        observacoes_mobilidade,
        id_func_social,
        responde_chamado,
        contato_visual,
        imita_acoes,
        participa_brincadeiras,
        respeita_turnos,
        fala_palavras,
        gestos_sinais,
        pede_ajuda,
        compreende_instrucoes,
        expressa_sentimento,
        guarda_brinquedo,
        lembra_atividades,
        cumpre_combinado,
        escolhe_roupas,
        demonstra_interesse,
        observacoes_fun_social
    FROM db_funcae.vw_quest_pedi""")

    dados = cur.fetchall()
    colunas = [desc[0] for desc in cur.description]  # pega nomes das colunas
    cur.close()

    if not dados:
        return "Nenhum dado para exportar.", 404

    # Cria DataFrame com nomes das colunas
    df = pd.DataFrame(dados, columns=colunas)

    # Cria Excel em memória
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='PDI')

    output.seek(0)

    # Retorna Excel para download
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='relatorio_pdi.xlsx'
    )



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
