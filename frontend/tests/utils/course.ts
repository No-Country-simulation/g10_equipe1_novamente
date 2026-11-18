// Note: the `PrivateService` is only available when generating the client
// for local environments
import { type PrivateCourseCreate, PrivateService } from "../../src/client"
import { client } from "../../src/client/client.gen"

client.setConfig({
  baseURL: `${process.env.VITE_API_URL}`,
})

export const createCourse = async (body: PrivateCourseCreate) => {
  const response = await PrivateService.createCourse({ body })
  return response.data
}
