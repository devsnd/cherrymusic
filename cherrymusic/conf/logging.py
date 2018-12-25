
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'formatters': {
        'magniloquent': {
            'format': (
                '[%(asctime)s] '
                '%(levelname)s '
                '[%(name)s:%(module)s.%(funcName)s:%(lineno)d] '
                '[%(process)d/%(thread)d] '
                '%(message)s'
            )
        },
        'verbose': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s] %(message)s'
        },
        'simple': {
            'format': '[%(asctime)s] %(levelname)s %(message)s'
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_false'],
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'debug_console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
        'parso.python.diff': {
            'level': 'INFO'
        }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console', 'debug_console'],
    },
}
