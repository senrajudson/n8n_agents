from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union
import statistics
import math
import re

import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
)

app = FastAPI(
    title="Math Tool",
    description="Ferramenta local para estatística, derivadas e integrais.",
    version="1.1.0"
)


class StatsRequest(BaseModel):
    values: List[float] = Field(..., description="Lista de valores numéricos.")
    operations: Optional[List[str]] = Field(
        default=None,
        description="Operações estatísticas desejadas."
    )


class CalculusRequest(BaseModel):
    operation: str = Field(
        ...,
        description="Operação: derivative, partial_derivative, integral ou double_integral."
    )
    expression: str = Field(..., description="Expressão matemática.")
    variables: List[str] = Field(..., description="Variáveis usadas na operação.")
    order: Optional[int] = Field(default=1, description="Ordem da derivada comum.")
    orders: Optional[List[int]] = Field(
        default=None,
        description="Ordens para derivadas parciais. Exemplo: [1, 2]."
    )
    bounds: Optional[Dict[str, List[Union[str, float, int]]]] = Field(
        default=None,
        description="Limites de integração. Exemplo: {'x': [0, 1]}."
    )
    simplify_result: bool = Field(default=True)
    numeric_approx: bool = Field(default=True)


ALLOWED_FUNCTIONS = {
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "asin": sp.asin,
    "acos": sp.acos,
    "atan": sp.atan,
    "sinh": sp.sinh,
    "cosh": sp.cosh,
    "tanh": sp.tanh,
    "exp": sp.exp,
    "log": sp.log,
    "ln": sp.log,
    "sqrt": sp.sqrt,
    "Abs": sp.Abs,
    "abs": sp.Abs,
}

ALLOWED_CONSTANTS = {
    "pi": sp.pi,
    "E": sp.E,
    "e": sp.E,
}

SAFE_GLOBALS = {
    "__builtins__": {},
    "Integer": sp.Integer,
    "Float": sp.Float,
    "Rational": sp.Rational,
    "Symbol": sp.Symbol,
}

TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)


def validate_values(values: List[float]) -> List[float]:
    if not values:
        raise ValueError("A lista de valores não pode estar vazia.")

    if len(values) > 100000:
        raise ValueError("A lista de valores é muito grande. Limite: 100000 valores.")

    clean_values = []

    for value in values:
        if not isinstance(value, (int, float)):
            raise ValueError("Todos os valores precisam ser numéricos.")

        if not math.isfinite(value):
            raise ValueError("A lista contém valor inválido, infinito ou NaN.")

        clean_values.append(float(value))

    return clean_values


def calculate_stats(values: List[float], operations: Optional[List[str]]) -> Dict[str, Any]:
    values = validate_values(values)

    available_operations = {
        "count",
        "sum",
        "mean",
        "median",
        "min",
        "max",
        "range",
        "variance_population",
        "variance_sample",
        "stddev_population",
        "stddev_sample"
    }

    if operations is None or len(operations) == 0:
        operations = sorted(list(available_operations))

    invalid_operations = [op for op in operations if op not in available_operations]

    if invalid_operations:
        raise ValueError(f"Operações inválidas: {invalid_operations}")

    result = {}

    if "count" in operations:
        result["count"] = len(values)

    if "sum" in operations:
        result["sum"] = sum(values)

    if "mean" in operations:
        result["mean"] = statistics.mean(values)

    if "median" in operations:
        result["median"] = statistics.median(values)

    if "min" in operations:
        result["min"] = min(values)

    if "max" in operations:
        result["max"] = max(values)

    if "range" in operations:
        result["range"] = max(values) - min(values)

    if "variance_population" in operations:
        result["variance_population"] = statistics.pvariance(values)

    if "stddev_population" in operations:
        result["stddev_population"] = statistics.pstdev(values)

    if "variance_sample" in operations:
        result["variance_sample"] = statistics.variance(values) if len(values) > 1 else None

    if "stddev_sample" in operations:
        result["stddev_sample"] = statistics.stdev(values) if len(values) > 1 else None

    return result


def text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def validate_variable_names(variables: List[str]) -> List[str]:
    if not variables:
        raise ValueError("Informe pelo menos uma variável.")

    clean_variables = []

    for variable in variables:
        variable = text(variable)

        if not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", variable):
            raise ValueError(f"Nome de variável inválido: {variable}")

        if variable in ALLOWED_FUNCTIONS or variable in ALLOWED_CONSTANTS:
            raise ValueError(f"Nome de variável reservado: {variable}")

        clean_variables.append(variable)

    return clean_variables


def build_local_dict(variables: List[str]) -> Dict[str, Any]:
    local_dict = {}

    for variable in variables:
        local_dict[variable] = sp.Symbol(variable, real=True)

    local_dict.update(ALLOWED_FUNCTIONS)
    local_dict.update(ALLOWED_CONSTANTS)

    return local_dict


def parse_math_expression(expression: Any, variables: List[str]) -> Any:
    expression_text = text(expression).replace("^", "**")

    if not expression_text:
        raise ValueError("Expressão vazia.")

    if len(expression_text) > 500:
        raise ValueError("Expressão muito longa. Limite: 500 caracteres.")

    blocked_tokens = ["__", "import", "exec", "eval", "lambda", "open", "os.", "sys."]
    lowered = expression_text.lower()

    for token in blocked_tokens:
        if token in lowered:
            raise ValueError("Expressão contém token bloqueado.")

    if not re.match(r"^[0-9A-Za-z_+\-*/().,\s]+$", expression_text):
        raise ValueError("Expressão contém caracteres não permitidos.")

    local_dict = build_local_dict(variables)
    allowed_names = set(local_dict.keys())

    names = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expression_text)

    invalid_names = [name for name in names if name not in allowed_names]

    if invalid_names:
        raise ValueError(f"Nomes não permitidos na expressão: {invalid_names}")

    return parse_expr(
        expression_text,
        local_dict=local_dict,
        global_dict=SAFE_GLOBALS,
        transformations=TRANSFORMATIONS,
        evaluate=True
    )


def parse_bound(value: Any, variables: List[str]) -> Any:
    return parse_math_expression(value, variables)


def has_unevaluated_calculus(result: Any) -> bool:
    return result.has(sp.Integral) or result.has(sp.Derivative)


def format_result(result: Any, simplify_result: bool, numeric_approx: bool) -> Dict[str, Any]:
    if simplify_result:
        result = sp.simplify(result)

    approximation = None

    if numeric_approx and not result.free_symbols and not has_unevaluated_calculus(result):
        try:
            approximation = float(sp.N(result))
        except Exception:
            approximation = None

    return {
        "result": str(result),
        "latex": sp.latex(result),
        "numeric_approx": approximation,
        "has_free_symbols": len(result.free_symbols) > 0,
        "has_unevaluated_calculus": has_unevaluated_calculus(result)
    }


def calculate_calculus(request: CalculusRequest) -> Dict[str, Any]:
    operation = text(request.operation).lower()
    variables = validate_variable_names(request.variables)
    expression = parse_math_expression(request.expression, variables)

    symbols = build_local_dict(variables)

    if operation == "derivative":
        variable = variables[0]
        order = request.order or 1

        if order < 1 or order > 10:
            raise ValueError("A ordem da derivada deve estar entre 1 e 10.")

        result = sp.diff(expression, symbols[variable], order)

        formatted = format_result(result, request.simplify_result, request.numeric_approx)
        formatted["operation"] = operation
        formatted["variable"] = variable
        formatted["order"] = order
        return formatted

    if operation == "partial_derivative":
        if request.orders is None:
            orders = [1 for _ in variables]
        else:
            orders = request.orders

        if len(orders) != len(variables):
            raise ValueError("A quantidade de ordens deve ser igual à quantidade de variáveis.")

        result = expression

        for variable, order in zip(variables, orders):
            if order < 1 or order > 10:
                raise ValueError("Cada ordem de derivada deve estar entre 1 e 10.")

            result = sp.diff(result, symbols[variable], order)

        formatted = format_result(result, request.simplify_result, request.numeric_approx)
        formatted["operation"] = operation
        formatted["variables"] = variables
        formatted["orders"] = orders
        return formatted

    if operation == "integral":
        variable = variables[0]
        bounds = request.bounds or {}

        if variable in bounds:
            if len(bounds[variable]) != 2:
                raise ValueError("O limite da integral precisa ter início e fim.")

            lower = parse_bound(bounds[variable][0], variables)
            upper = parse_bound(bounds[variable][1], variables)

            result = sp.integrate(expression, (symbols[variable], lower, upper))
        else:
            result = sp.integrate(expression, symbols[variable])

        formatted = format_result(result, request.simplify_result, request.numeric_approx)
        formatted["operation"] = operation
        formatted["variable"] = variable
        formatted["bounds"] = bounds
        return formatted

    if operation == "double_integral":
        if len(variables) != 2:
            raise ValueError("Para integral dupla, informe exatamente duas variáveis.")

        bounds = request.bounds or {}
        integration_args = []

        for variable in variables:
            if variable in bounds:
                if len(bounds[variable]) != 2:
                    raise ValueError(f"O limite da variável {variable} precisa ter início e fim.")

                lower = parse_bound(bounds[variable][0], variables)
                upper = parse_bound(bounds[variable][1], variables)

                integration_args.append((symbols[variable], lower, upper))
            else:
                integration_args.append(symbols[variable])

        result = sp.integrate(expression, *integration_args)

        formatted = format_result(result, request.simplify_result, request.numeric_approx)
        formatted["operation"] = operation
        formatted["variables"] = variables
        formatted["bounds"] = bounds
        return formatted

    raise ValueError("Operação inválida. Use derivative, partial_derivative, integral ou double_integral.")


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "math_tool"
    }


@app.post("/stats")
def stats(request: StatsRequest):
    try:
        result = calculate_stats(request.values, request.operations)

        return {
            "ok": True,
            "input_count": len(request.values),
            "operations": request.operations,
            "result": result
        }

    except Exception as error:
        return {
            "ok": False,
            "error": str(error)
        }


@app.post("/calculus")
def calculus(request: CalculusRequest):
    try:
        result = calculate_calculus(request)

        return {
            "ok": True,
            "input": {
                "operation": request.operation,
                "expression": request.expression,
                "variables": request.variables,
                "order": request.order,
                "orders": request.orders,
                "bounds": request.bounds
            },
            "result": result
        }

    except Exception as error:
        return {
            "ok": False,
            "error": str(error)
        }