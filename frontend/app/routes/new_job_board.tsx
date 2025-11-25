import { Form, Link, redirect, useFetcher } from "react-router";
import type { Route } from "../+types/root";
import { Field, FieldGroup, FieldLabel, FieldLegend } from "~/components/ui/field";
import { Input } from "~/components/ui/input";
import { Button } from "~/components/ui/button";

export async function clientAction({ request }: Route.ClientActionArgs) {
  const formData = await request.formData()
  await fetch('/api/job-boards', {
    method: 'POST',
    body: formData,
  })
  return redirect('/job-boards')
} 

export default function NewJobBoardForm(_: Route.ComponentProps) {
  return (
    <div className="w-full max-w-md">
      <Form method="post" encType="multipart/form-data">
        <FieldGroup>
          <FieldLegend>Add New Job Board</FieldLegend>
          <Field>
            <FieldLabel htmlFor="slug">
              Slug
            </FieldLabel>
            <Input
              id="slug"
              name="slug"
              placeholder="acme"
              required
            />
          </Field>
          <Field>
            <FieldLabel htmlFor="logo">
              Logo
            </FieldLabel>
            <Input
              id="logo"
              name="logo"
              type="file"
              required
            />
          </Field>
          <div className="float-right">
            <Field orientation="horizontal">
              <Button type="submit">Submit</Button>
              <Button variant="outline" type="button">
                <Link to="/job-boards">Cancel</Link>
              </Button>
            </Field>
          </div>
        </FieldGroup>
      </Form>
    </div>
  );
}