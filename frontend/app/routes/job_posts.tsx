import { Link } from "react-router";
import { Button } from "~/components/ui/button";

export async function clientLoader({params}) {
  const res = await fetch(`/api/job-boards/${params.jobBoardId}/job-posts`);
  const jobPosts = await res.json();
  return {jobPosts}
}

export default function JobPosts({loaderData}) {
  return (
    <div>
      {loaderData.jobPosts.map(
        (jobPost) => 
          <div>
            <div className="flex items-center justify-between">
              <h2 key={jobPost.id} className="text-3xl font-bold">{jobPost.title}</h2>
              <Button>
                <Link to={`/job-posts/${jobPost.id}/application`}>Apply</Link>
              </Button>
            </div>
            <p className="mt-2">{jobPost.description}</p>
          </div>
      )}
    </div>
  )
}

