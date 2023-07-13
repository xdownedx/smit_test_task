from fastapi import FastAPI
import json
from tortoise import Tortoise, fields
from tortoise.models import Model
from tortoise.contrib.fastapi import register_tortoise
from pydantic import BaseModel
from datetime import date, datetime

app = FastAPI()

class InsuranceRate(Model):
    id = fields.IntField(pk=True)
    cargo_type = fields.CharField(max_length=255)
    rate = fields.DecimalField(max_digits=5, decimal_places=3)
    effective_date = fields.DateField(default=date.today)

    class Meta:
        table = 'insurance_rate'



class InsuranceRateResponse(BaseModel):
    rate: float

@app.get('/insurance/{date}/{cargo_type}/{declared_value}')
async def calculate_insurance_cost(date: str, cargo_type: str, declared_value:float):
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
    except:
        return {'error': 'Incorrect date'}
    object = await InsuranceRate.filter(cargo_type=cargo_type, effective_date=date_obj).first()
    if object:
        return {"insurance_cost":float(object.rate) * declared_value}
    return {'error': 'No tariff was found for the specified cargo type and date'}


@app.on_event('startup')
async def startup():
    await Tortoise.init(
        db_url='postgres://postgres:password@db:5432/postgres',  # замените на соответствующие настройки
        modules={'models': ['main']},
    )
    await Tortoise.generate_schemas()

    # Очистка таблицы InsuranceRate
    await InsuranceRate.all().delete()

    # Загрузка данных из файла JSON
    with open('rates.json') as file:
        data = json.load(file)

    for date_str, rates in data.items():
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        for rate_data in rates:
            cargo_type = rate_data['cargo_type']
            rate_value = rate_data['rate']
            await InsuranceRate.create(cargo_type=cargo_type, rate=rate_value, effective_date=date_obj)




@app.on_event('shutdown')
async def shutdown():
    await Tortoise.close_connections()


register_tortoise(
    app,
    db_url='postgres://postgres:password@db:5432/postgres',  # замените на соответствующие настройки
    modules={'models': ['main']},
    generate_schemas=True,
    add_exception_handlers=True,
)
