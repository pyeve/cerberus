import uuid


P_TYPES = ['ONE', 'TWO']
T_TYPES = ['NO', 'V20']


def to_bool(value):
    return value.lower() in ('true', '1')


def allowed_tax(value):
    return value if value.upper() in T_TYPES else 'NO'


def allowed_types(value):
    return value if value.upper() in P_TYPES else 'ONE'


def none_to_zero(value):
    return 0 if value in (None, "") else value


def empty_str_to_null(value):
    return None if value == '' else value


product_schema = {
    'uuid': {
        'type': 'string',
        'required': True,
        'nullable': False,
        'default_setter': lambda x: uuid.uuid4().__str__(),
    },
    'name': {
        'type': 'string',
        'minlength': 1,
        'maxlength': 100,
        'required': True,
        'nullable': False,
        'default': 'noname product',
    },
    'group': {
        'type': 'boolean',
        'required': False,
        'nullable': False,
        'default': False,
    },
    'parentUuid': {
        'type': 'string',
        'required': False,
        'nullable': True,
        'default': None,
    },
    'hasVariants': {
        'type': 'boolean',
        'required': False,
        'nullable': False,
        'default': False,
    },
    'type': {
        'type': 'string',
        'required': True,
        'allowed': P_TYPES,
        'nullable': False,
        'default': 'ONE',
        'coerce': allowed_types,
    },
    'quantity': {
        'type': 'float',
        'required': True,
        'nullable': False,
        'default': 0,
        'coerce': (none_to_zero, float),
    },
    'measureName': {
        'type': 'string',
        'required': True,
        'nullable': False,
        'default': '',
        'coerce': str,
    },
    'tax': {
        'type': 'string',
        'required': True,
        'allowed': T_TYPES,
        'nullable': False,
        'default': 'NO',
        'coerce': allowed_tax,
    },
    'price': {
        'type': 'float',
        'required': True,
        'min': 0,
        'max': 9999999.99,
        'nullable': False,
        'default': 0,
        'coerce': (none_to_zero, float),
    },
    'allowToSell': {
        'type': 'boolean',
        'required': True,
        'nullable': False,
        'default': True,
        'coerce': (str, to_bool),
    },
    'costPrice': {
        'type': 'float',
        'min': 0,
        'max': 9999999.99,
        'required': True,
        'nullable': False,
        'default': 0,
        'coerce': (none_to_zero, float),
    },
    'description': {
        'type': 'string',
        'minlength': 0,
        'required': False,
        'nullable': True,
        'default': '',
        'coerce': str,
    },
    'articleNumber': {
        'type': 'string',
        'minlength': 0,
        'maxlength': 20,
        'required': False,
        'nullable': True,
        'coerce': (empty_str_to_null, lambda s: str(s)[0:19]),
        'default': '',
    },
    'code': {
        'type': 'string',
        'minlength': 0,
        'maxlength': 10,
        'required': True,
        'coerce': (empty_str_to_null, lambda s: str(s)[0:9]),
        'default': '',
    },
    'barCodes': {'type': 'list', 'required': True, 'nullable': True, 'default': []},
    'alcoCodes': {'type': 'list', 'required': True, 'nullable': True, 'default': []},
    'alcoholByVolume': {
        'type': ['float', 'string'],
        'required': True,
        'nullable': True,
        'default': None,
        'coerce': (empty_str_to_null, float),
    },
    'alcoholProductKindCode': {
        'type': ['float', 'string'],
        'required': True,
        'nullable': True,
        'default': None,
        'coerce': (empty_str_to_null, int),
    },
    'tareVolume': {
        'type': ['float', 'string'],
        'required': True,
        'nullable': True,
        'default': None,
        'coerce': (empty_str_to_null, float),
    },
}
