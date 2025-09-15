import { AfterSaveBotApi, WireRecord } from "@uesio/bots"

type SeriesCache = Record<string, Record<string, number> | undefined>

export default function manage_ordering(bot: AfterSaveBotApi) {
  // Figure out which serieses need processing
  const seriesesToProcess: SeriesCache = {}

  bot.inserts.get().forEach((change) => {
    const currentOrder = change.get("uesio/cms.order") as number
    const currentSeries = change.get(
      "uesio/cms.series->uesio/core.id",
    ) as string
    const currentId = change.get("uesio/core.id") as string

    let seriesToProcess = seriesesToProcess[currentSeries]

    if (!seriesToProcess) {
      seriesesToProcess[currentSeries] = {}
      seriesToProcess = seriesesToProcess[currentSeries]
    }

    seriesToProcess[currentId] = currentOrder
  })

  bot.updates.get().forEach((change) => {
    const currentOrder = change.getOld("uesio/cms.order") as number
    const currentSeries = change.get(
      "uesio/cms.series->uesio/core.id",
    ) as string
    const currentId = change.get("uesio/core.id") as string

    const changes = change.getAll()
    const currentOrderRequest = changes["uesio/cms.order"] as number
    const hasCurrentValue = currentOrderRequest || currentOrderRequest === 0
    if (hasCurrentValue && currentOrderRequest !== currentOrder) {
      let seriesToProcess = seriesesToProcess[currentSeries]

      if (!seriesToProcess) {
        seriesesToProcess[currentSeries] = {}
        seriesToProcess = seriesesToProcess[currentSeries]
      }

      seriesToProcess[currentId] = currentOrderRequest
    }
  })

  bot.deletes.get().forEach((change) => {
    const currentSeries = change.getOld(
      "uesio/cms.series->uesio/core.id",
    ) as string
    const seriesToProcess = seriesesToProcess[currentSeries]

    if (!seriesToProcess) {
      seriesesToProcess[currentSeries] = {}
    }
  })

  const seriesKeys = Object.keys(seriesesToProcess)

  if (!seriesKeys.length) {
    //bot.log.info("We're done!")
    return
  }

  //bot.log.info("process",seriesesToProcess)

  // Now do a query for all the tracks we need to process
  const result = bot.load({
    collection: "uesio/cms.series_track",
    fields: [
      {
        id: "uesio/cms.order",
      },
      {
        id: "uesio/cms.series",
        fields: [
          {
            id: "uesio/core.id",
          },
        ],
      },
    ],
    conditions: [
      {
        field: "uesio/cms.series",
        operator: "IN",
        values: seriesKeys,
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

  // Now put our tracks into buckes by series
  const currentSerieses: SeriesCache = {}

  result.forEach((track) => {
    const currentSeries = track["uesio/cms.series"] as string // This is bad
    const currentOrder = track["uesio/cms.order"] as number
    const currentId = track["uesio/core.id"] as string
    let seriesToProcess = currentSerieses[currentSeries]

    if (!seriesToProcess) {
      currentSerieses[currentSeries] = {}
      seriesToProcess = currentSerieses[currentSeries]
    }

    seriesToProcess[currentId] = currentOrder
  })

  //bot.log.info("current",currentSerieses)

  const updates: WireRecord[] = []

  // Now loop over our current serieses and put in a correct order
  Object.keys(currentSerieses).forEach((seriesId) => {
    let index = 0
    const currentSeries = currentSerieses[seriesId]
    if (!currentSeries) {
      return
    }
    const processSeries = seriesesToProcess[seriesId]
    // Make a map keyed off of request for this series
    const requestsByIndex: Record<number, string> = {}
    const requestsById: Record<string, number> = {}
    // Make a map of successful order requests
    const successes: Record<string, boolean> = {}
    if (processSeries) {
      Object.keys(processSeries).forEach((trackId) => {
        const requestTrack = processSeries[trackId]
        if (requestTrack || requestTrack === 0) {
          requestsByIndex[requestTrack] = trackId
          requestsById[trackId] = requestTrack
        }
      })
    }

    //bot.log.info("requests2",requestsByIndex)

    Object.keys(currentSeries).forEach((trackId) => {
      const currentTrack = currentSeries[trackId]

      if (requestsByIndex[index]) {
        // Someone wants this slot
        updates.push({
          ["uesio/core.id"]: requestsByIndex[index],
          ["uesio/cms.order"]: index,
        } as unknown as WireRecord)
        successes[requestsByIndex[index]] = true
        index++
      }
      if (successes[trackId] || requestsById[trackId]) {
        return
      }
      if (currentTrack !== index) {
        updates.push({
          ["uesio/core.id"]: trackId,
          ["uesio/cms.order"]: index,
        } as unknown as WireRecord)
      }
      index++
    })
  })

  //bot.log.info("updates",updates)

  bot.save("uesio/cms.series_track", updates)
}
