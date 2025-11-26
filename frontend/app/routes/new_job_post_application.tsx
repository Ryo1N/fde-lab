import { Form, redirect } from "react-router";
import { Button } from "~/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "~/components/ui/card";
import { Field, FieldGroup, FieldLabel } from "~/components/ui/field";
import { Input } from "~/components/ui/input";
import { cn } from "~/lib/utils";

export async function clientLoader({params}) {
  const jobPostId = params.jobPostId
  return {jobPostId}
}

export async function clientAction({ request }: Route.ClientActionArgs) {
  const formData = await request.formData()
  await fetch('/api/job-applications', {
    method: 'POST',
    body: formData,
  })
  return redirect('/job-boards')
} 

export default function NewJobApplicationForm({
  loaderData,
  className,
  ...props
}) {
  return (
    <div className={cn("flex flex-col gap-6 w-1/2 mx-auto mt-4", className)} {...props}>
      <Card>
        <CardHeader>
          <CardTitle>New Job Application</CardTitle>
        </CardHeader>
        <CardContent>
          <Form method="post" encType="multipart/form-data">
            <input type="hidden" name="job_post_id" value={loaderData.jobPostId}/>
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="first_name">First Name</FieldLabel>
                <Input
                  id="first_name"
                  name="first_name"
                  type="text"
                  required
                />
              </Field>
              <Field>
                <FieldLabel htmlFor="last_name">Last Name</FieldLabel>
                <Input
                  id="last_name"
                  name="last_name"
                  type="text"
                  required
                />
              </Field>
              <Field>
                <FieldLabel htmlFor="email">Email</FieldLabel>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  required
                />
              </Field>
              <Field>
              <FieldLabel htmlFor="resume">
                Resume
              </FieldLabel>
              <Input
                id="resume"
                name="resume"
                type="file"
                required
              />
            </Field>
              <Field>
                <Button type="submit">Submit</Button>
              </Field>
            </FieldGroup>
          </Form>
        </CardContent>
      </Card>
    </div>
  )
}