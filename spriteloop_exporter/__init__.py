from krita import DockWidgetFactory, DockWidgetFactoryBase, Krita

from .docker import SpriteLoopExporterDocker
from .extension import SpriteLoopExporterExtension


app = Krita.instance()
app.addExtension(SpriteLoopExporterExtension(app))
app.addDockWidgetFactory(
    DockWidgetFactory(
        "spriteloop_exporter_docker",
        DockWidgetFactoryBase.DockRight,
        SpriteLoopExporterDocker,
    )
)
