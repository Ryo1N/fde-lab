import { layout, route, type RouteConfig } from "@react-router/dev/routes";

export default [
  layout("layouts/default.tsx", [
    route("/", "routes/home.tsx"),
    route("job-boards", "routes/job_boards.tsx"),
    route("job-boards/new", "routes/new_job_board.tsx"),
    route("job-boards/:jobBoardId/job-posts", "routes/job_posts.tsx")
  ])
] satisfies RouteConfig;

