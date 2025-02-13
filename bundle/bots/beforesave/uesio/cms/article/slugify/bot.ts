import { BeforeSaveBotApi } from "@uesio/bots"

function slugify(bot: BeforeSaveBotApi) {
	const changes = [...bot.inserts.get(), ...bot.updates.get()]
	changes.forEach((r) => {
		// If no slug, slugify the title
		const slug = r.get("uesio/cms.slug") as string
		if (!slug) {
			const title = r.get("uesio/cms.name") as string
			if (!title) throw new Error("Missing title")
			return r.set(
				"uesio/cms.slug",
				title
					.toLowerCase()
					.replace(/ /g, "-")
					.replace(/[^\w-]+/g, ""),
			)
		}

		// Remove whitespaces at start and end + check structure
		const sanitizedSlug = slug.replace(/^\s\s*/, "").replace(/\s\s*$/, "")
		const isValidSlug = /^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$/.test(
			sanitizedSlug,
		)
		if (!isValidSlug) throw new Error("Invalid slug: " + slug)

		r.set("uesio/cms.slug", sanitizedSlug)
	})
}
