#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <p99/p99.h>

typedef struct {
    PyObject_HEAD
    p99_histogram_t histogram;
} HistogramObject;

static PyObject*
histogram_new(PyTypeObject* type, PyObject* args, PyObject* kwds)
{
    HistogramObject* self;

    (void)args;
    (void)kwds;

    self = (HistogramObject*)type->tp_alloc(type, 0);
    if (self == NULL) {
        return NULL;
    }

    p99_histogram_init(&self->histogram);
    return (PyObject*)self;
}

static void
histogram_dealloc(HistogramObject* self)
{
    Py_TYPE(self)->tp_free((PyObject*)self);
}

static PyObject*
histogram_clear(HistogramObject* self, PyObject* Py_UNUSED(ignored))
{
    p99_histogram_clear(&self->histogram);
    Py_RETURN_NONE;
}

static PyObject*
optional_u64_from_truthy(p99_truthy_t ok, uint64_t value)
{
    if (!ok) {
        Py_RETURN_NONE;
    }

    return PyLong_FromUnsignedLongLong(value);
}

static PyObject*
optional_u64_from_out_param(
    p99_truthy_t (*query)(p99_histogram_t const*, uint64_t*),
    HistogramObject* self
)
{
    uint64_t value;
    p99_truthy_t ok = query(&self->histogram, &value);

    return optional_u64_from_truthy(ok, value);
}

static PyObject*
optional_u64_from_out_param_index(
    p99_truthy_t (*query)(p99_histogram_t const*, size_t, uint64_t*),
    HistogramObject* self,
    size_t index
)
{
    uint64_t value;
    p99_truthy_t ok = query(&self->histogram, index, &value);

    return optional_u64_from_truthy(ok, value);
}

static PyObject*
optional_u64_from_out_param_percentile(
    p99_truthy_t (*query)(p99_histogram_t const*, double, uint64_t*),
    HistogramObject* self,
    double percentile
)
{
    uint64_t value;
    p99_truthy_t ok = query(&self->histogram, percentile, &value);

    return optional_u64_from_truthy(ok, value);
}

static PyObject*
histogram_push_ns(HistogramObject* self, PyObject* args)
{
    unsigned long long time_in_ns;

    if (!PyArg_ParseTuple(args, "K", &time_in_ns)) {
        return NULL;
    }

    return PyBool_FromLong(
        p99_histogram_push_event_time_ns(&self->histogram, (uint64_t)time_in_ns)
    );
}

static PyObject*
histogram_push_us(HistogramObject* self, PyObject* args)
{
    unsigned long long time_in_us;

    if (!PyArg_ParseTuple(args, "K", &time_in_us)) {
        return NULL;
    }

    return PyBool_FromLong(
        p99_histogram_push_event_time_us(&self->histogram, (uint64_t)time_in_us)
    );
}

static PyObject*
histogram_push_ms(HistogramObject* self, PyObject* args)
{
    unsigned long long time_in_ms;

    if (!PyArg_ParseTuple(args, "K", &time_in_ms)) {
        return NULL;
    }

    return PyBool_FromLong(
        p99_histogram_push_event_time_ms(&self->histogram, (uint64_t)time_in_ms)
    );
}

static PyObject*
histogram_push_s(HistogramObject* self, PyObject* args)
{
    unsigned long long time_in_s;

    if (!PyArg_ParseTuple(args, "K", &time_in_s)) {
        return NULL;
    }

    return PyBool_FromLong(
        p99_histogram_push_event_time_s(&self->histogram, (uint64_t)time_in_s)
    );
}

static PyObject*
histogram_get_event_count(HistogramObject* self, void* Py_UNUSED(closure))
{
    return PyLong_FromUnsignedLongLong(
        p99_histogram_event_count(&self->histogram)
    );
}

static PyObject*
histogram_get_has_overflowed(HistogramObject* self, void* Py_UNUSED(closure))
{
    return PyBool_FromLong(
        p99_histogram_has_overflowed(&self->histogram)
    );
}

static PyObject*
histogram_event_time_total(HistogramObject* self, PyObject* Py_UNUSED(ignored))
{
    return optional_u64_from_out_param(p99_histogram_event_time_total, self);
}

static PyObject*
histogram_event_time_total_raw(HistogramObject* self, PyObject* Py_UNUSED(ignored))
{
    return PyLong_FromUnsignedLongLong(
        p99_histogram_event_time_total_raw(&self->histogram)
    );
}

static PyObject*
histogram_min_ns(HistogramObject* self, PyObject* Py_UNUSED(ignored))
{
    return optional_u64_from_out_param(p99_histogram_min_event_time, self);
}

static PyObject*
histogram_max_ns(HistogramObject* self, PyObject* Py_UNUSED(ignored))
{
    return optional_u64_from_out_param(p99_histogram_max_event_time, self);
}

static PyObject*
histogram_bucket_value(HistogramObject* self, PyObject* args)
{
    Py_ssize_t index;

    if (!PyArg_ParseTuple(args, "n", &index)) {
        return NULL;
    }

    return optional_u64_from_out_param_index(
        p99_histogram_bucket_value,
        self,
        (size_t)index
    );
}

static PyObject*
histogram_buckets_view(HistogramObject* self, PyObject* Py_UNUSED(ignored))
{
    PyObject* tuple;
    p99_bucket_count_t const* buckets;
    size_t i;

    buckets = p99_histogram_buckets(&self->histogram);
    tuple = PyTuple_New(P99_BUCKET_COUNT);
    if (tuple == NULL) {
        return NULL;
    }

    for (i = 0; i < P99_BUCKET_COUNT; ++i) {
        PyObject* item = PyLong_FromUnsignedLongLong((unsigned long long)buckets[i]);
        if (item == NULL) {
            Py_DECREF(tuple);
            return NULL;
        }
        PyTuple_SET_ITEM(tuple, (Py_ssize_t)i, item);
    }

    return tuple;
}

static PyObject*
histogram_value_at_percentile(HistogramObject* self, PyObject* args)
{
    double percentile;

    if (!PyArg_ParseTuple(args, "d", &percentile)) {
        return NULL;
    }

    return optional_u64_from_out_param_percentile(
        p99_histogram_value_at_percentile,
        self,
        percentile
    );
}

#define HISTOGRAM_VALUE_AT_P(name, c_fn)                                    \
    static PyObject*                                                        \
    name(HistogramObject* self, PyObject* Py_UNUSED(ignored))               \
    {                                                                       \
        return optional_u64_from_out_param(c_fn, self);                     \
    }

HISTOGRAM_VALUE_AT_P(histogram_value_at_p50, p99_histogram_value_at_p50)
HISTOGRAM_VALUE_AT_P(histogram_value_at_p75, p99_histogram_value_at_p75)
HISTOGRAM_VALUE_AT_P(histogram_value_at_p90, p99_histogram_value_at_p90)
HISTOGRAM_VALUE_AT_P(histogram_value_at_p95, p99_histogram_value_at_p95)
HISTOGRAM_VALUE_AT_P(histogram_value_at_p99, p99_histogram_value_at_p99)
HISTOGRAM_VALUE_AT_P(histogram_value_at_p99_5, p99_histogram_value_at_p99_5)
HISTOGRAM_VALUE_AT_P(histogram_value_at_p99_9, p99_histogram_value_at_p99_9)
HISTOGRAM_VALUE_AT_P(histogram_value_at_p99_99, p99_histogram_value_at_p99_99)
HISTOGRAM_VALUE_AT_P(histogram_value_at_p99_999, p99_histogram_value_at_p99_999)
HISTOGRAM_VALUE_AT_P(histogram_value_at_p99_999_9, p99_histogram_value_at_p99_999_9)

static PyObject*
histogram_values_at_percentiles(HistogramObject* self, PyObject* args)
{
    PyObject* levels_seq;
    PyObject* result = NULL;
    Py_ssize_t length;
    Py_ssize_t i;

    if (!PyArg_ParseTuple(args, "O", &levels_seq)) {
        return NULL;
    }

    if (!PySequence_Check(levels_seq)) {
        PyErr_SetString(PyExc_TypeError, "levels must be a sequence");
        return NULL;
    }

    length = PySequence_Length(levels_seq);
    if (length < 0) {
        return NULL;
    }

    if (length == 0) {
        if (p99_histogram_event_count(&self->histogram) == 0) {
            Py_RETURN_NONE;
        }
        return PyList_New(0);
    }

    if (p99_histogram_event_count(&self->histogram) == 0) {
        Py_RETURN_NONE;
    }

    result = PyList_New(length);
    if (result == NULL) {
        return NULL;
    }

    for (i = 0; i < length; ++i) {
        PyObject* level_obj = PySequence_GetItem(levels_seq, i);
        PyObject* item;
        double level;
        uint64_t value;

        if (level_obj == NULL) {
            Py_DECREF(result);
            return NULL;
        }

        level = PyFloat_AsDouble(level_obj);
        Py_DECREF(level_obj);
        if (PyErr_Occurred()) {
            Py_DECREF(result);
            return NULL;
        }

        {
            p99_truthy_t ok = p99_histogram_value_at_percentile(
                &self->histogram,
                level,
                &value
            );

            if (!ok) {
                Py_DECREF(result);
                Py_RETURN_NONE;
            }
        }

        item = Py_BuildValue("(dK)", level, (unsigned long long)value);
        if (item == NULL) {
            Py_DECREF(result);
            return NULL;
        }
        PyList_SET_ITEM(result, i, item);
    }

    return result;
}

static const char* const fixed_percentile_keys[10] = {
    "p50",
    "p75",
    "p90",
    "p95",
    "p99",
    "p99.5",
    "p99.9",
    "p99.99",
    "p99.999",
    "p99.9999",
};

typedef PyObject* (*histogram_getter_fn)(HistogramObject*, PyObject*);

static PyObject*
histogram_fixed_percentiles(HistogramObject* self, PyObject* Py_UNUSED(ignored))
{
    PyObject* dict;
    size_t i;
    histogram_getter_fn getters[10] = {
        histogram_value_at_p50,
        histogram_value_at_p75,
        histogram_value_at_p90,
        histogram_value_at_p95,
        histogram_value_at_p99,
        histogram_value_at_p99_5,
        histogram_value_at_p99_9,
        histogram_value_at_p99_99,
        histogram_value_at_p99_999,
        histogram_value_at_p99_999_9,
    };

    if (p99_histogram_event_count(&self->histogram) == 0) {
        Py_RETURN_NONE;
    }

    dict = PyDict_New();
    if (dict == NULL) {
        return NULL;
    }

    for (i = 0; i < 10; ++i) {
        PyObject* value = getters[i](self, NULL);
        if (value == NULL) {
            Py_DECREF(dict);
            return NULL;
        }
        if (PyDict_SetItemString(dict, fixed_percentile_keys[i], value) < 0) {
            Py_DECREF(value);
            Py_DECREF(dict);
            return NULL;
        }
        Py_DECREF(value);
    }

    return dict;
}

static PyGetSetDef Histogram_getsetters[] = {
    {"event_count", (getter)histogram_get_event_count, NULL, NULL, NULL},
    {"has_overflowed", (getter)histogram_get_has_overflowed, NULL, NULL, NULL},
    {NULL}
};

static PyMethodDef Histogram_methods[] = {
    {"clear", (PyCFunction)histogram_clear, METH_NOARGS, NULL},
    {"push_ns", (PyCFunction)histogram_push_ns, METH_VARARGS, NULL},
    {"push_us", (PyCFunction)histogram_push_us, METH_VARARGS, NULL},
    {"push_ms", (PyCFunction)histogram_push_ms, METH_VARARGS, NULL},
    {"push_s", (PyCFunction)histogram_push_s, METH_VARARGS, NULL},
    {"event_time_total", (PyCFunction)histogram_event_time_total, METH_NOARGS, NULL},
    {"event_time_total_raw", (PyCFunction)histogram_event_time_total_raw, METH_NOARGS, NULL},
    {"min_ns", (PyCFunction)histogram_min_ns, METH_NOARGS, NULL},
    {"max_ns", (PyCFunction)histogram_max_ns, METH_NOARGS, NULL},
    {"bucket_value", (PyCFunction)histogram_bucket_value, METH_VARARGS, NULL},
    {"buckets_view", (PyCFunction)histogram_buckets_view, METH_NOARGS, NULL},
    {"value_at_percentile", (PyCFunction)histogram_value_at_percentile, METH_VARARGS, NULL},
    {"value_at_p50", (PyCFunction)histogram_value_at_p50, METH_NOARGS, NULL},
    {"value_at_p75", (PyCFunction)histogram_value_at_p75, METH_NOARGS, NULL},
    {"value_at_p90", (PyCFunction)histogram_value_at_p90, METH_NOARGS, NULL},
    {"value_at_p95", (PyCFunction)histogram_value_at_p95, METH_NOARGS, NULL},
    {"value_at_p99", (PyCFunction)histogram_value_at_p99, METH_NOARGS, NULL},
    {"value_at_p99_5", (PyCFunction)histogram_value_at_p99_5, METH_NOARGS, NULL},
    {"value_at_p99_9", (PyCFunction)histogram_value_at_p99_9, METH_NOARGS, NULL},
    {"value_at_p99_99", (PyCFunction)histogram_value_at_p99_99, METH_NOARGS, NULL},
    {"value_at_p99_999", (PyCFunction)histogram_value_at_p99_999, METH_NOARGS, NULL},
    {"value_at_p99_999_9", (PyCFunction)histogram_value_at_p99_999_9, METH_NOARGS, NULL},
    {"values_at_percentiles", (PyCFunction)histogram_values_at_percentiles, METH_VARARGS, NULL},
    {"fixed_percentiles", (PyCFunction)histogram_fixed_percentiles, METH_NOARGS, NULL},
    {NULL}
};

static PyTypeObject HistogramType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "p99.Histogram",
    .tp_basicsize = sizeof(HistogramObject),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = histogram_new,
    .tp_dealloc = (destructor)histogram_dealloc,
    .tp_methods = Histogram_methods,
    .tp_getset = Histogram_getsetters,
};

static struct PyModuleDef extmodule = {
    PyModuleDef_HEAD_INIT,
    .m_name = "p99._ext",
    .m_size = -1,
};

PyMODINIT_FUNC
PyInit__ext(void)
{
    PyObject* module;

    if (PyType_Ready(&HistogramType) < 0) {
        return NULL;
    }

    module = PyModule_Create(&extmodule);
    if (module == NULL) {
        return NULL;
    }

    Py_INCREF(&HistogramType);
    if (PyModule_AddObject(module, "Histogram", (PyObject*)&HistogramType) < 0) {
        Py_DECREF(&HistogramType);
        Py_DECREF(module);
        return NULL;
    }

    return module;
}
