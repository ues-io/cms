import { AfterSaveBotApi, WireRecord } from "@uesio/bots"

type TrackCache = Record<string, Record<string, number> | undefined>

export default function manage_ordering(bot: AfterSaveBotApi) {
  // Figure out which tracks need processing
  const tracksToProcess: TrackCache = {}

  bot.inserts.get().forEach((change) => {
    const currentOrder = change.get("uesio/cms.order") as number
    const currentTrack = change.get("uesio/cms.track->uesio/core.id") as string
    const currentId = change.get("uesio/core.id") as string

    let trackToProcess = tracksToProcess[currentTrack]

    if (!trackToProcess) {
      tracksToProcess[currentTrack] = {}
      trackToProcess = tracksToProcess[currentTrack]
    }

    trackToProcess[currentId] = currentOrder
  })

  bot.updates.get().forEach((change) => {
    const currentOrder = change.getOld("uesio/cms.order") as number
    const currentTrack = change.get("uesio/cms.track->uesio/core.id") as string
    const currentId = change.get("uesio/core.id") as string

    const changes = change.getAll()
    const currentOrderRequest = changes["uesio/cms.order"] as number
    const hasCurrentValue = currentOrderRequest || currentOrderRequest === 0
    if (hasCurrentValue && currentOrderRequest !== currentOrder) {
      let trackToProcess = tracksToProcess[currentTrack]

      if (!trackToProcess) {
        tracksToProcess[currentTrack] = {}
        trackToProcess = tracksToProcess[currentTrack]
      }

      trackToProcess[currentId] = currentOrderRequest
    }
  })

  bot.deletes.get().forEach((change) => {
    const currentTrack = change.getOld(
      "uesio/cms.track->uesio/core.id",
    ) as string
    const trackToProcess = tracksToProcess[currentTrack]

    if (!trackToProcess) {
      tracksToProcess[currentTrack] = {}
    }
  })

  const trackKeys = Object.keys(tracksToProcess)

  if (!trackKeys.length) {
    //bot.log.info("We're done!")
    return
  }

  //bot.log.info("process",tracksToProcess)

  // Now do a query for all the articles we need to process
  const result = bot.load({
    collection: "uesio/cms.track_article",
    fields: [
      {
        id: "uesio/cms.order",
      },
      {
        id: "uesio/cms.track",
        fields: [
          {
            id: "uesio/core.id",
          },
        ],
      },
    ],
    conditions: [
      {
        field: "uesio/cms.track",
        operator: "IN",
        values: trackKeys,
      },
    ],
    order: [
      {
        field: "uesio/cms.order",
        desc: false,
      },
    ],
  })

  //bot.log.info("result",result)

  // Now put our articles into buckes by track
  const currentTracks: TrackCache = {}

  result.forEach((article) => {
    const currentTrack = article["uesio/cms.track"] as string // This is bad
    const currentOrder = article["uesio/cms.order"] as number
    const currentId = article["uesio/core.id"] as string
    let trackToProcess = currentTracks[currentTrack]

    if (!trackToProcess) {
      currentTracks[currentTrack] = {}
      trackToProcess = currentTracks[currentTrack]
    }

    trackToProcess[currentId] = currentOrder
  })

  //bot.log.info("current",currentTracks)

  const updates: WireRecord[] = []

  // Now loop over our current tracks and put in a correct order
  Object.keys(currentTracks).forEach((trackId) => {
    let index = 0
    const currentTrack = currentTracks[trackId]
    if (!currentTrack) {
      return
    }
    const processTrack = tracksToProcess[trackId]
    // Make a map keyed off of request for this track
    const requestsByIndex: Record<number, string> = {}
    const requestsById: Record<string, number> = {}
    // Make a map of successful order requests
    const successes: Record<string, boolean> = {}
    if (processTrack) {
      Object.keys(processTrack).forEach((articleId) => {
        const requestArticle = processTrack[articleId]
        if (requestArticle || requestArticle === 0) {
          requestsByIndex[requestArticle] = articleId
          requestsById[articleId] = requestArticle
        }
      })
    }

    //bot.log.info("requests2",requestsByIndex)

    Object.keys(currentTrack).forEach((articleId) => {
      const currentArticle = currentTrack[articleId]

      if (requestsByIndex[index]) {
        // Someone wants this slot
        updates.push({
          ["uesio/core.id"]: requestsByIndex[index],
          ["uesio/cms.order"]: index,
        } as unknown as WireRecord)
        successes[requestsByIndex[index]] = true
        index++
      }
      if (successes[articleId] || requestsById[articleId]) {
        return
      }
      if (currentArticle !== index) {
        updates.push({
          ["uesio/core.id"]: articleId,
          ["uesio/cms.order"]: index,
        } as unknown as WireRecord)
      }
      index++
    })
  })

  //bot.log.info("updates",updates)

  bot.save("uesio/cms.track_article", updates)
}
