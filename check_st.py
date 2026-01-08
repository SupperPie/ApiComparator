import streamlit as st
import inspect

print(f"Streamlit version: {st.__version__}")
sig = inspect.signature(st.data_editor)
print("st.data_editor parameters:")
for name in sig.parameters:
    print(f"- {name}")
