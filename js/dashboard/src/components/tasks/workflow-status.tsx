import { Badge } from "@/components/ui/badge";
import { workflowStatusEnum, WorkflowStatus } from "./data/schema";

export function WorkflowStatusDisplay(props: {
  status: WorkflowStatus;
}): React.JSX.Element {
  switch (props.status) {
    case workflowStatusEnum.Enum.RUNNING:
      return <Badge>Running</Badge>;
    case workflowStatusEnum.Enum.SUSPENDED:
      return <Badge variant="outline">Suspended</Badge>;
    case workflowStatusEnum.Enum.FAILED:
      return <Badge variant="destructive">Failed</Badge>;
    case workflowStatusEnum.Enum.CANCELLED:
      return <Badge variant="outline">Cancelled</Badge>;
    case workflowStatusEnum.Enum.COMPLETED:
      return <Badge variant="secondary">Completed</Badge>;
    case workflowStatusEnum.Enum.TERMINATED:
      return <Badge variant="destructive">Terminated</Badge>;
    case workflowStatusEnum.Enum.TIMED_OUT:
      return <Badge variant="outline">Timed Out</Badge>;
    case workflowStatusEnum.Enum.CONTINUED_AS_NEW:
      return <Badge>Continued As New</Badge>;
  }
}
