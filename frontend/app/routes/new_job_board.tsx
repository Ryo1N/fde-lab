import { useFetcher } from "react-router";
import type { Route } from "../+types/root";
import { Field, FieldGroup, FieldLabel, FieldLegend } from "~/components/ui/field";
import { Input } from "~/components/ui/input";
import { Button } from "~/components/ui/button";

export default function Signup(_: Route.ComponentProps) {
  let fetcher = useFetcher();
  return (
    <div className="w-full max-w-md">
      <fetcher.Form method="post">
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
                Cancel
              </Button>
            </Field>
          </div>
        </FieldGroup>
      </fetcher.Form>
    </div>
  );
}