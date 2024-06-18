from fixpoint_extras.workflows import structured


@structured.workflow(id="example_workflow")
class Foo:
    def bazinga(self) -> None:
        pass


if __name__ == "__main__":
    structured.run_workflow(Foo, [])
