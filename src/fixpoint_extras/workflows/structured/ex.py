from .workflow import workflow, run_workflow

@workflow(id="example_workflow")
class Foo:
    def bazinga(self):
        pass

if __name__ == '__main__':
    run_workflow(Foo, [])
