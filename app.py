import re
from bson import ObjectId
from flask import Flask, redirect, render_template, request, url_for, flash


app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'
import pymongo

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
# Acessa o banco de dados
mydb = myclient["dbMeccanotecnica"]
# Acessa a coleção
mycol = mydb["Products"]
validateAccess = True



@app.route("/")
def home():
    if(validateAccess):
        table_data = buscarDados()
        return render_template("index.html", table_data=table_data)
    else:
        return render_template("login.html")


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
    return redirect(url_for("home"))


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
        return render_template("index.html", table_data=table_data, value_search=item)
    else:
        return redirect(url_for("home"))



@app.route("/deletar/<id>", methods=["POST"])
def deletar(id):
    object_id = ObjectId(id)
    myquery = {"_id": object_id}
    result = mycol.delete_one(myquery)
    if result.deleted_count > 0:
        return redirect(url_for("home"))
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
        return redirect(url_for("home"))


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
    return redirect(url_for("home"))



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



if __name__ == "__main__":
    app.run(debug=True)
