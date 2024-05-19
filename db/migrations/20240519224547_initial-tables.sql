-- migrate:up
CREATE TABLE fixpoint.workflows(
  id UUID PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE fixpoint.chat_completion_inputs(
  id UUID PRIMARY KEY,
  workflow_id UUID REFERENCES fixpoint.workflows(id),
  session_id UUID NULL,
  provider TEXT NOT NULL,
  model TEXT NOT NULL,
  request JSONB NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),    
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE fixpoint.chat_completion_outputs(
  id UUID PRIMARY KEY,
  input_id UUID REFERENCES fixpoint.chat_completion_inputs(id),
  workflow_id UUID REFERENCES fixpoint.workflows(id),
  session_id UUID NULL,
  response JSONB NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION fixpoint.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_workflows_modtime
BEFORE UPDATE ON fixpoint.workflows
FOR EACH ROW
EXECUTE PROCEDURE fixpoint.update_updated_at_column();

CREATE TRIGGER update_chat_completion_inputs_modtime
BEFORE UPDATE ON fixpoint.chat_completion_inputs
FOR EACH ROW
EXECUTE PROCEDURE fixpoint.update_updated_at_column();

CREATE TRIGGER update_chat_completion_outputs_modtime
BEFORE UPDATE ON fixpoint.chat_completion_outputs
FOR EACH ROW
EXECUTE PROCEDURE fixpoint.update_updated_at_column();

-- migrate:down
DROP TRIGGER update_workflows_modtime ON fixpoint.workflows;
DROP TRIGGER update_chat_completion_inputs_modtime ON fixpoint.chat_completion_inputs;
DROP TRIGGER update_chat_completion_outputs_modtime ON fixpoint.chat_completion_outputs;
DROP FUNCTION fixpoint.update_updated_at_column;
DROP TABLE fixpoint.chat_completion_outputs;
DROP TABLE fixpoint.chat_completion_inputs;
DROP TABLE fixpoint.workflows;
