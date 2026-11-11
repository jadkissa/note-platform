# Notes

A single-host lab for running a small notes app the way a service is run: an image, more than one container, a published front door, and state kept off the container.

The workload is a Python app that writes notes to Postgres. Docker Compose on this laptop is the runtime. Nginx is the edge. The app is stateless and runs as two copies. Postgres is the only stateful service, and its data sits on a named volume.

This first setup stops at Docker, Nginx, a database, and a simple load balancer. Kubernetes, MetalLB, a private registry, and Terraform are the next environment, on an Ubuntu VM, after this one is ordinary.

## Runtime

Everything runs as containers on the laptop. Compose is the unit you start and stop: one file brings up Nginx, two app containers, and Postgres, and tears them down together.

| Concern | How this lab handles it |
| --- | --- |
| Build | An image is a snapshot. `notes:1` and `notes:2` are two builds of the same page, so a rebuild is a new artifact, not a live edit |
| Run | A container is a running copy of an image. Deleting it removes the process and leaves mounted data behind |
| Edge | Nginx publishes `8080` on the laptop and proxies `/` to the app |
| Scale | Two app containers sit behind one Nginx `upstream`. A refresh can land on either copy |
| State | Postgres uses a named volume. Replacing the database container keeps the `notes` table |
| Network | Only Nginx is reachable from the laptop. The app and Postgres talk on the Compose network |

## Request path

```text
Browser :8080
  → Nginx (published)
    → app copy A or app copy B (Compose network only)
      → Postgres (named volume)
```

Nginx is the load balancer: one front door, two copies behind it. Each app container prints its own name on the page, so a few refreshes show both names while the notes stay the same. Both copies share one database, so which copy answered does not change what was saved.

`docker compose down` followed by `docker compose up` replaces the containers. The note is still there because the volume, not the container, is the disk.

## What each part is for

- **Image.** The package you build and run. A bind mount shows files live. A build freezes them into the image.
- **App container.** Replaceable. It serves the form and the list, and it opens no host port.
- **Nginx.** The only published port. It hides the app and spreads traffic across the two copies.
- **Postgres.** The system of record. The container can be thrown away. The named volume cannot, if the data is meant to survive.
- **Compose.** One description of the whole stack: who publishes a port, who talks to whom, and which volume outlives a restart.

## After this host

The same service moves to an Ubuntu VM. The next objects are a Kubernetes Pod, then the rest of that cluster one object at a time, then MetalLB, a private registry, and Terraform. Those are a later plan. They are not part of the Compose stack on this laptop.
