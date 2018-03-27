# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

import json
import pickle
import decimal
import os.path
from sklearn import tree
from json import JSONEncoder
from bson import ObjectId
import logging
import io
from pymongo import MongoClient
from django.core.files import File
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from . models import employees
from . serializers import employeeSerializer
# Create your views here.

BASE = os.path.dirname(os.path.abspath(__file__))
D = decimal.Decimal
ingredientsPath = os.path.join(BASE, "ingredients_list.json")
recipesPath = os.path.join(BASE, "recipes.json")
ingredients = json.load(io.open(ingredientsPath, 'r',encoding='utf-8'))['ingredients_list']
recipes = json.load(io.open(recipesPath,'r', encoding='utf-8'))['recipes']    # Creating dictionaries with the necessary data

ingredientsList = []
for key in sorted(list(ingredients.keys())):
    ingredientsList.append({
        'name': key,
        'measurements': ingredients[key]
    })


volume = ['tablespoon', 'cup', 'pinch', 'quart']
volume_mes = [3, 48, 0.0625, 192]
mes_list = ["n/a", "can", "bag", "bar", "clove", "packet", "ounce", "loaf", "loaves", "package", "teaspoon", "square",
            "container"]
categories_list = ['Desserts', 'World Cuisine', 'Breakfast and Brunch', 'Bread', 'Side Dish', 'Recipes', 'Meat and Poultry', 'Trusted Brands: Recipes and Tips', 'Everyday Cooking', 'Salad', 'Main Dish', 'Soups, Stews and Chili', 'Appetizers and Snacks', 'Pasta and Noodles', 'Drinks', 'Ingredients', 'Healthy Recipes', 'Seafood', 'Holidays and Events', 'Fruits and Vegetables']



features = []
labels = []
labels2 = []
picklePath1 = os.path.join(BASE, "save1.pkl")
picklePath2 = os.path.join(BASE, "save2.pkl")
clf1 = pickle.load(open(picklePath1, 'rb'))
clf2 = pickle.load(open(picklePath2, 'rb'))

def recipe_to_data(recipe):
    array = [0] * len(ingredients) *3
    for i in recipe['ingredients']:
            num = list(ingredients.keys()).index(i['name'])
            raw_quant = i['quantity']
            if type(raw_quant) == type('test'):
                quant = 1 if 'n/a' in raw_quant.lower() else raw_quant
            else:
                quant = raw_quant
            raw_mes = i['measurement'].lower()
            if raw_mes == 'loaves':
                raw_mes = 'loaf'
            raw_mes = raw_mes[:-1] if raw_mes.endswith('s') else raw_mes
            if raw_mes in volume:
                mes = 'teaspoon'
                quant = quant*volume_mes[volume.index(raw_mes)]
            elif 'pound' in raw_mes:
                mes = 'ounce'
                quant = quant*16
            else:
                mes = raw_mes
            mes_index = mes_list.index(mes)
            try:
                array[num*3] = array[num*3] + quant
            except Exception:
                print quant
            array[num*3+1] = mes_index
            if i['required']:
                array[num*3+2] = 1

    return array

def init(n):
    for i in range(0, n):
                features.append(recipe_to_data(recipes[i]))
                labels.append(round(recipes[i]['rating']*10))
                labels2.append(categories_list.index(recipes[i]['category']))

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


class Recipe(APIView):
    parser_classes = (JSONParser,)
    def get(self, request):
        return Response(ingredientsList)

    def post(self, request):
        query = request.data
        for obj in query:
            keys = list(obj.keys())
            for i in keys:
                try:
                    if type(obj[i]) == type('test'):
                        obj[i.encode('utf-8')] = obj.pop(i).encode('utf-8')
                    else:
                        obj[i.encode('utf-8')] = obj.pop(i)
                except Exception:
                    pass
        for obj in query:
            obj['quantity'] = float(obj['quantity'])
        recipe = {'ingredients': query}
        output = list(clf1.predict([recipe_to_data(recipe)]))
        output.append(categories_list[list(clf2.predict([recipe_to_data(recipe)]))[0]])
        return Response(output)

def index(request):
    return render(request, 'index.html')

def result(request):
    return render(request, 'result.html')
