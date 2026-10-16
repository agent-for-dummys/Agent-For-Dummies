"""Restricted Python API surface for local function exercises."""
import ast
import builtins
import math
import torch
import torch.nn as nn
import torch.nn.functional as F

IMPORTS={'torch','torch.nn','torch.nn.functional','torch.nn.utils.rnn','torch.utils.data','math'}
IMPORTS.update({'torch.optim','torch.nn.utils'})
IMPORTS.update({'torch.linalg', 'torch.special'})
ATTRS=set('tensor arange zeros ones empty full zeros_like ones_like full_like rand randn randint manual_seed float32 float64 int64 long bool Tensor nn optim utils rnn data functional pad_sequence DataLoader TensorDataset Linear Embedding from_pretrained Parameter SGD zero_grad step parameters weight bias shape dtype device ndim size dim numel view reshape permute transpose t T mT contiguous clone detach requires_grad_ requires_grad grad backward float double long to sum mean std square pow norm amax max min clamp clamp_min abs sqrt exp log logsumexp masked_fill masked_fill_ where isfinite unsqueeze squeeze expand expand_as repeat gather scatter scatter_ sort argsort topk cumsum cat stack tril triu matmul bmm mm einsum eye equal allclose any all tolist item flatten normalize linear cross_entropy mse_loss softmax log_softmax relu sigmoid tanh scaled_dot_product_attention append extend get items keys values copy count index pop pi e'.split())
ATTRS.update({'no_grad','enable_grad','cpu','is_tensor','autograd'})
ATTRS.update('linspace meshgrid index_select nonzero argmax argmin scatter_add_ bincount one_hot conv2d max_pool2d avg_pool2d AdamW clip_grad_norm_ Dropout eval train copy_ layer_norm gelu binary_cross_entropy_with_logits reshape_as'.split())
ATTRS.add('var')
ATTRS.add('embedding')
# Normal CPU tensor operations should not be mistaken for unavailable APIs.
# Keep storage, file I/O, dynamic imports and Python internals outside this surface.
ATTRS.update('amin aminmax indices as_tensor asarray tensor_split split chunk unbind narrow select take take_along_dim index_copy index_copy_ index_add index_add_ scatter_add scatter_reduce scatter_reduce_ scatter_reduce prod cumprod cummax cummin logcumsumexp median nanmedian quantile nanquantile nanmean nansum nan_to_num isnan isinf isposinf isneginf isclose std_mean var_mean float16 bfloat16 int8 int16 int32 uint8 complex64 complex128 real imag angle conj resolve_conj complex polar finfo iinfo get_default_dtype type_as bool int short half bfloat16 element_size is_floating_point is_complex is_contiguous stride storage_offset unflatten movedim moveaxis swapaxes swapdims reshape_as view_as broadcast_to broadcast_tensors broadcast_shapes repeat_interleave tile roll flip fliplr flipud rot90 diagonal diag diag_embed trace tril_indices triu_indices vstack hstack dstack column_stack concatenate concat atleast_1d atleast_2d atleast_3d logspace empty_like empty_strided new_tensor new_zeros new_ones new_empty new_full rand_like randn_like randperm normal bernoulli multinomial unique unique_consecutive searchsorted bucketize histc histogram eq ne gt ge lt le logical_and logical_or logical_xor logical_not bitwise_and bitwise_or bitwise_xor bitwise_not logical_and_ logical_or_ add add_ sub sub_ mul mul_ div div_ divide true_divide floor_divide remainder fmod neg positive maximum minimum fmax fmin clamp_max clip clamp_ clamp_min_ clamp_max_ square_ reciprocal rsqrt sign sgn ceil floor trunc frac round lerp addcmul addcdiv exp2 expm1 log2 log10 log1p logaddexp logaddexp2 sin cos tan asin acos atan atan2 sinh cosh asinh acosh atanh erf erfc lgamma digamma hypot dot vdot inner outer tensordot addmm addbmm baddbmm mv addmv linalg special vector_norm matrix_norm det slogdet inv pinv solve lstsq svd svdvals qr eig eigh eigvals eigvalsh cholesky cholesky_ex matrix_rank matrix_power diagflat eye is_grad_enabled set_grad_enabled inference_mode retain_grad register_hook requires_grad functional interpolate pad dropout dropout2d leaky_relu elu silu softplus softsign hardtanh hardsigmoid hardswish relu6 relu_ softmax softmin logsigmoid smooth_l1_loss l1_loss nll_loss kl_div huber_loss cosine_similarity pairwise_distance adaptive_avg_pool2d adaptive_max_pool2d avg_pool1d max_pool1d conv1d conv3d max_pool3d avg_pool3d batch_norm group_norm instance_norm pixel_shuffle pixel_unshuffle unfold fold sequential Sequential ModuleList ModuleDict Identity ReLU GELU SiLU Sigmoid Tanh Softmax LogSoftmax LayerNorm BatchNorm1d BatchNorm2d Conv1d Conv2d Conv3d MaxPool2d AvgPool2d AdaptiveAvgPool2d Flatten LSTM GRU RNN MSELoss CrossEntropyLoss BCEWithLogitsLoss Adam RMSprop Adagrad momentum nesterov named_parameters named_buffers buffers state_dict load_state_dict zero_ fill_ uniform_ normal_ init xavier_uniform_ xavier_normal_ kaiming_uniform_ kaiming_normal_ constant_ ones_ zeros_ calculate_gain sqrt ceil floor isclose isnan isinf log2 log10 expm1 log1p sin cos tan atan2 inf nan'.split())
BUILTIN_NAMES='sorted reversed all any iter next slice map filter int float bool str list tuple dict set frozenset complex divmod pow repr format'
ATTRS.update('expit logit entr xlogy xlog1py ndtr ndtri log_ndtr erfinv erfcx gammaln gammainc gammaincc multigammaln polygamma zeta i0 i1 i0e i1e sinc softmax log_softmax'.split())
ATTRS.update('eps tiny resolution bits maxexp minexp masked_select masked_scatter masked_scatter_ is_nonzero count_nonzero isreal detach_ requires_grad_ squeeze_ unsqueeze_ transpose_ t_ addmm_ addmv_ scatter_add_ flatten_ round_ floor_ ceil_ trunc_ frac_ reciprocal_ rsqrt_ lerp_ eq_ ne_ lt_ le_ gt_ ge_ sinc sinc_ heaviside triu_ tril_ triu tril unbind unflatten deg2rad rad2deg degrees radians tanh cosh sinh acos asin atan acosh asinh atanh fsum logaddexp2'.split())
BUILTINS={name:getattr(builtins,name) for name in 'print range enumerate zip len sum min max abs round int float bool str list tuple dict set isinstance Exception ValueError RuntimeError NotImplementedError'.split()}
BUILTINS.update({name:getattr(builtins,name) for name in BUILTIN_NAMES.split()})

class PolicyError(ValueError): pass

def validate(code, problem=None):
    if len(code.encode('utf-8'))>20000:raise PolicyError('代码最多 20 KB。')
    tree=ast.parse(code,filename='<submission>')
    calls=set()
    for node in ast.walk(tree):
        if isinstance(node,(ast.ClassDef,ast.Global,ast.Nonlocal,ast.AsyncFunctionDef,ast.Await,ast.Yield,ast.YieldFrom)):
            raise PolicyError('本题使用函数接口，不支持类、异步或全局声明。')
        if isinstance(node,ast.Name) and node.id.startswith('__'):raise PolicyError('不能访问 Python 内部对象。')
        if isinstance(node,ast.Attribute) and node.attr not in ATTRS:raise PolicyError(f'当前练习环境不支持属性或函数：{node.attr}')
        if isinstance(node,ast.Import):
            if any(alias.name not in IMPORTS for alias in node.names):raise PolicyError('只允许导入本课程使用的 torch 和 math 模块。')
        if isinstance(node,ast.ImportFrom):
            if node.level or node.module not in IMPORTS or any(a.name not in ATTRS for a in node.names):raise PolicyError('不支持这个导入。')
        if isinstance(node,ast.Call):
            name=node.func.attr if isinstance(node.func,ast.Attribute) else node.func.id if isinstance(node.func,ast.Name) else ''
            calls.add(name)
            for keyword in node.keywords:
                if keyword.arg=='num_workers' and not (isinstance(keyword.value,ast.Constant) and keyword.value.value==0):raise PolicyError('DataLoader 仅支持 num_workers=0。')
    if problem:
        if not any(isinstance(n,ast.FunctionDef) and n.name==problem['entry'] for n in tree.body):raise PolicyError(f'请保留函数签名 {problem["signature"]}')
        missing=set(problem.get('requiredCalls',[]))-calls
        if missing:raise PolicyError('本题要求使用：'+', '.join(sorted(missing)))
        forbidden=set(problem.get('forbiddenCalls',[]))&calls
        if forbidden:raise PolicyError('本题需要手动实现，不能调用：'+', '.join(sorted(forbidden)))
    return tree

def safe_import(name,globals=None,locals=None,fromlist=(),level=0):
    # Tensor repr uses this internal import from C++; student AST imports still use IMPORTS.
    if level or name not in IMPORTS|{'torch.storage'}:raise PolicyError('不支持这个导入。')
    return builtins.__import__(name,globals,locals,fromlist,0)

def namespace():
    return {'__builtins__':{**BUILTINS,'__import__':safe_import},'torch':torch,'nn':nn,'F':F,'math':math}
