import config
import display
import agent

_layer_idx = 0
def init():
    global _layer_idx
    _layer_idx = 0
    print("[macros] {} layers".format(len(config.MACRO_LAYERS)))


def current_layer():
    layers = config.MACRO_LAYERS
    if not layers:
        return {"name": "None", "b": "", "c": ""}
    return layers[_layer_idx % len(layers)]


def layer_name():
    return current_layer().get("name", "?")


def cycle_layer():
    global _layer_idx
    layers = config.MACRO_LAYERS
    if not layers:
        return
    _layer_idx = (_layer_idx + 1) % len(layers)
    name = layer_name()
    print("[macros] layer →", name)
    display.show_overlay("Layer: " + name, 2000)


def fire_b():
    action = current_layer().get("b", "")
    if action:
        agent.send_macro(action, layer_name())
        display.show_overlay(current_layer().get("name", "") + " · B", 800)


def fire_c():
    action = current_layer().get("c", "")
    if action:
        agent.send_macro(action, layer_name())
        display.show_overlay(current_layer().get("name", "") + " · C", 800)
