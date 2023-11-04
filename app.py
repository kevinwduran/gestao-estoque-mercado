import re
import pymongo
from bson import ObjectId
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["dbMeccanotecnica"]
mycol = mydb["Products"]
mycol2 = mydb["Users"]

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, username):
        self.username = username
        self.nivel = self.get_user_nivel(username)

    def get_id(self):
        return self.username
    
    def get_user_nivel(self, username):
        user_data = mycol2.find_one({"username": username})
        if user_data:
            return user_data.get("nivel")
        return None

@login_manager.user_loader
def load_user(username):
    user_data = mycol2.find_one({"username": username})
    if user_data:
        user = User(username)
        return user

@app.route('/')
@login_required
def home():
    table_data = buscarProdutosAbaixoEstoqueMinimo()
    return render_template("index.html", table_data=table_data)


@app.route('/users')
@login_required
def users():
    table_data = userBuscarDados()
    return render_template("users.html", table_data=table_data)

@app.route('/products')
@login_required
def products():
    table_data = buscarDados()
    return render_template("products.html", table_data=table_data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_data = mycol2.find_one({"username": username, "password": password})

        if user_data:
            user = User(username)
            login_user(user)
            print("Login bem-sucedido", "success")
            return redirect(url_for('home')) 
        else:
            print("Credenciais inválidas. Tente novamente.", "error")

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()  # Limpa a sessão do usuário
    return redirect(url_for('login'))

# CRUD PRODUTOS
@app.route("/", methods=["POST"])
def cadastrar():

    nome = request.form["nome"]
    codigo = request.form["codigo"]
    estoqueMin = request.form["estoqueMin"]
    categoria = request.form["categoria"]
    preco = request.form["preco"]
    quantidade = request.form["quantidade"]
    unidadeMedida = request.form["unidadeMedida"]
    status = request.form["status"]
    
    # Verifica se o código já existe no banco de dados
    existing_item = mycol.find_one({"codigo": codigo})
    if existing_item:
        flash("Código já existe. Escolha um código diferente.", "error")
        return redirect(url_for("home"))

    avulso = {
        "nome": nome,
        "codigo": codigo,
        "estoqueMin": estoqueMin,
        "categoria": categoria,
        "preco": preco,
        "quantidade": quantidade,
        "unidadeMedida": unidadeMedida,
        "status": status,
    }
    x = mycol.insert_one(avulso)
    return redirect(url_for("products"))


@app.route("/buscar", methods=["POST"])
def buscaritens():
    item = request.form["buscar-item"]
    search_option = request.form["search-option"]

    if item:
        regex_pattern = re.compile(re.escape(item), re.IGNORECASE)
        myquery = {
            search_option: {"$regex": regex_pattern}
        }
        mydoc = mycol.find(myquery)

        results = []

        for x in mydoc:
            results.append(x)

        table_data = []

        for result in results:
            table_data.append(
                [
                    result.get("_id"),
                    result.get("nome", ""),
                    result.get("codigo", ""),
                    result.get("estoqueMin", ""),
                    result.get("categoria", ""),
                    result.get("preco", ""),
                    result.get("quantidade", ""),
                    result.get("unidadeMedida", ""),
                    result.get("status", ""),
                ]
            )
        return render_template("products.html", table_data=table_data, value_search=item)
    else:
        return redirect(url_for("products"))



@app.route("/deletar/<id>", methods=["POST"])
def deletar(id):
    object_id = ObjectId(id)
    myquery = {"_id": object_id}
    result = mycol.delete_one(myquery)
    if result.deleted_count > 0:
        return redirect(url_for("products"))
    else:
        return "não tem registro"


@app.route("/alterar/<id>", methods=["GET"])
def alterar(id):
    if id:
        object_id = ObjectId(id)
        myquery = {"_id": object_id}
        item_data = mycol.find_one(myquery)

        if item_data:
            nome = item_data.get("nome", "")
            codigo = item_data.get("codigo", "")
            estoqueMin = item_data.get("estoqueMin", "")
            categoria = item_data.get("categoria", "")
            preco = item_data.get("preco", "")
            quantidade = item_data.get("quantidade", "")
            unidadeMedida = item_data.get("unidadeMedida", "")
            status = item_data.get("status", "")

            return render_template(
                "alterItens.html",
                id=id,
                nome=nome,
                codigo=codigo,
                estoqueMin=estoqueMin,
                categoria=categoria,
                preco=preco,
                quantidade=quantidade,
                unidadeMedida=unidadeMedida,
                status=status,
            )
        else:
            return "Item não encontrado"
    else:
        return redirect(url_for("products"))


@app.route("/salvarAlteracoes", methods=["POST"])
def salvarAlteracoes():
    id = request.form["id"]
    nome = request.form["nome"]
    codigo = request.form["codigo"]
    estoqueMin = request.form["estoqueMin"]
    categoria = request.form["categoria"]
    preco = request.form["preco"]
    quantidade = request.form["quantidade"]
    unidadeMedida = request.form["unidadeMedida"]
    status = request.form["status"]
    
    object_id = ObjectId(id)
    paraModificar = {"_id": object_id}
    novoValor = {
        "$set": {
            "nome": nome,
            "codigo": codigo,
            "estoqueMin": estoqueMin,
            "categoria": categoria,
            "preco": preco,
            "quantidade": quantidade,
            "unidadeMedida": unidadeMedida,
            "status": status,
        }
    }

    # Verifica se o código foi alterado
    item_data = mycol.find_one({"_id": object_id})
    if item_data:
        if item_data.get("codigo") != codigo:
            existing_item = mycol.find_one({"codigo": codigo})
            if existing_item:
                flash("Código já existe. Escolha um código diferente.", "error")
                return redirect(url_for("alterar", id=id))  # Redireciona de volta à página de alteração

    mycol.update_one(paraModificar, novoValor)
    return redirect(url_for("products"))

def buscarProdutosAbaixoEstoqueMinimo():
    produtos_abaixo_estoque_minimo = mycol.find()
    table_data = []

    for produto in produtos_abaixo_estoque_minimo:
        quantidade = int(produto.get("quantidade", "0"))
        estoque_min = int(produto.get("estoqueMin", "0"))

        if quantidade < estoque_min:
            table_data.append(
                [
                    produto.get("_id"),
                    produto.get("nome", ""),
                    produto.get("codigo", ""),
                    estoque_min,
                    produto.get("categoria", ""),
                    produto.get("preco", ""),
                    quantidade,
                    produto.get("unidadeMedida", ""),
                    produto.get("status", ""),
                ]
            )

    return table_data



def buscarDados():
    all_data = mycol.find()

    table_data = []

    for data in all_data:
        table_data.append(
            [
                data.get("_id"),
                data.get("nome", ""),
                data.get("codigo", ""),
                data.get("estoqueMin", ""),
                data.get("categoria", ""),
                data.get("preco", ""),
                data.get("quantidade", ""),
                data.get("unidadeMedida", ""),
                data.get("status", ""),
            ]
        )
    return table_data

# Usuários (CRUD)

@app.route("/userCadastrar", methods=["POST"])
def userCadastrar():

    username = request.form["username"]
    password = request.form["password"]
    nivel = request.form["nivel"]
    
    # Verifica se o código já existe no banco de dados
    existing_item = mycol2.find_one({"username": username})
    if existing_item:
        flash("Usuário já existe. Escolha um Usuário diferente.", "error")
        return redirect(url_for("users"))

    avulso = {
        "username": username,
        "password": password,
        "nivel": nivel,
    }
    x = mycol2.insert_one(avulso)
    return redirect(url_for("users"))




@app.route("/userDeletar/<id>", methods=["POST"])
def userDeletar(id):
    object_id = ObjectId(id)
    myquery = {"_id": object_id}
    result = mycol2.delete_one(myquery)
    if result.deleted_count > 0:
        return redirect(url_for("users"))
    else:
        return "não tem registro"


@app.route("/userAlterar/<id>", methods=["GET"])
def userAlterar(id):
    if id:
        object_id = ObjectId(id)
        myquery = {"_id": object_id}
        item_data = mycol2.find_one(myquery)

        if item_data:
            username = item_data.get("username", "")
            password = item_data.get("password", "")
            nivel = item_data.get("nivel", "")

            return render_template(
                "alterUsers.html",
                id=id,
                username=username,
                password=password,
                nivel=nivel,
            )
        else:
            return "Usuário não encontrado"
    else:
        return redirect(url_for("users"))


@app.route("/userSalvarAlteracoes", methods=["POST"])
def userSalvarAlteracoes():
    id = request.form["id"]
    username = request.form["username"]
    password = request.form["password"]
    nivel = request.form["nivel"]
    
    object_id = ObjectId(id)
    paraModificar = {"_id": object_id}
    novoValor = {
        "$set": {
            "username": username,
            "password": password,
            "nivel": nivel,
        }
    }

    # Verifica se o código foi alterado
    item_data = mycol2.find_one({"_id": object_id})
    if item_data:
        if item_data.get("username") != username:
            existing_item = mycol2.find_one({"username": username})
            if existing_item:
                flash("Código já existe. Escolha um username diferente.", "error")
                return redirect(url_for("userAlterar", id=id))  # Redireciona de volta à página de alteração

    mycol2.update_one(paraModificar, novoValor)
    return redirect(url_for("users"))



def userBuscarDados():
    all_data = mycol2.find()

    table_data = []

    for data in all_data:
        table_data.append(
            [
                data.get("_id"),
                data.get("username", ""),
                data.get("password", ""),
                data.get("nivel", ""),
            ]
        )
    return table_data

@app.context_processor
def utility_processor():
    user_level = None
    if current_user.is_authenticated:
        user_level = current_user.nivel
    return dict(user_level=user_level)

if __name__ == "__main__":
    app.run(debug=True)