class ErroRegraNegocio(Exception):
    pass


class ErroItemNaoEncontrado(ErroRegraNegocio):
    pass


class ErroCodigoItemInvalido(ErroRegraNegocio):
    pass


class ErroEstoqueNegativo(ErroRegraNegocio):
    pass


class ErroNivelBOMInvalido(ErroRegraNegocio):
    pass


class ErroCicloBOM(ErroRegraNegocio):
    pass


class ErroEstoqueComponenteInsuficiente(ErroRegraNegocio):
    pass


class ErroEstadoOrdem(ErroRegraNegocio):
    pass


class ErroCentroTrabalhoNaoEncontrado(ErroRegraNegocio):
    pass


class ErroValidacao(ErroRegraNegocio):
    pass
