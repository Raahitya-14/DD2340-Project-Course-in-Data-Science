import sionna, pkgutil

def walk_packages(package, level=1):
    """List submodules up to a given depth level."""
    def _walk(pkg, path, depth):
        if depth > level:
            return
        for module in pkgutil.iter_modules(path):
            full_name = f"{pkg.__name__}.{module.name}"
            print(full_name)
            if module.ispkg:  # if it's a package, go deeper
                _walk(__import__(full_name, fromlist=[""] ), 
                      __import__(full_name, fromlist=[""] ).__path__, 
                      depth+1)

    _walk(package, package.__path__, 1)

# Example: list up to 2 levels of submodules
walk_packages(sionna, level=4)
