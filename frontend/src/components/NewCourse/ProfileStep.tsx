import { useQuery } from "@tanstack/react-query"
import { ArrowRight } from "lucide-react"
import { useState } from "react"
import { type AudienceLevel, NichesService } from "@/client"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { AUDIENCE_LABELS } from "@/lib/courses"

export interface ProfileDraft {
  title: string
  nicheId: number | null
  audienceLevel: AudienceLevel | null
}

interface ProfileStepProps {
  profile: ProfileDraft
  onChange: (profile: ProfileDraft) => void
  onBack: () => void
  onContinue: () => void
}

const audienceOptions = [
  [
    "non_technical",
    "Iniciante ou gestor. Sem jargão, com analogias do dia a dia.",
  ],
  [
    "technical_basic",
    "Dev júnior ou pleno. Termos explicados e passos práticos.",
  ],
  [
    "technical_advanced",
    "Líder técnico ou arquiteto. Direto ao ponto, com limites e custos.",
  ],
] as const satisfies ReadonlyArray<readonly [AudienceLevel, string]>

function titleError(title: string) {
  const trimmed = title.trim()
  if (!trimmed) return "Informe um título."
  if (Array.from(trimmed).length > 255)
    return "O título passa de 255 caracteres."
  return null
}

export function ProfileStep({
  profile,
  onChange,
  onBack,
  onContinue,
}: ProfileStepProps) {
  const [checkedTitle, setCheckedTitle] = useState(false)
  const niches = useQuery({
    queryKey: ["niches"],
    queryFn: async () => (await NichesService.readNiches()).data,
    retry: false,
  })
  const error = checkedTitle ? titleError(profile.title) : null
  const nichesUnavailable =
    niches.isPending || niches.isFetching || niches.isError
  const selectedNiche = niches.data?.find(
    (niche) => niche.id === profile.nicheId,
  )

  return (
    <>
      <div className="flex flex-col gap-6 px-6">
        <div className="grid gap-2">
          <Label htmlFor="course-title">Título do curso</Label>
          <Input
            id="course-title"
            value={profile.title}
            aria-invalid={!!error}
            aria-describedby={error ? "course-title-error" : undefined}
            onBlur={() => setCheckedTitle(true)}
            onChange={(event) =>
              onChange({ ...profile, title: event.target.value })
            }
          />
          {error && (
            <p id="course-title-error" className="text-sm text-destructive">
              {error}
            </p>
          )}
        </div>
        <div className="grid gap-2">
          <Label htmlFor="course-niche">Setor</Label>
          <Select
            disabled={nichesUnavailable}
            value={selectedNiche?.id.toString() ?? ""}
            onValueChange={(value) =>
              onChange({ ...profile, nicheId: Number(value) })
            }
          >
            <SelectTrigger
              id="course-niche"
              className="w-full"
              aria-describedby={
                niches.isError ? "course-niche-error" : undefined
              }
            >
              <SelectValue
                placeholder={
                  niches.isFetching ? "Carregando setores…" : "Escolha um setor"
                }
              />
            </SelectTrigger>
            <SelectContent>
              {niches.data?.map((niche) => (
                <SelectItem key={niche.id} value={String(niche.id)}>
                  {niche.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {niches.isError && (
            <div className="flex flex-wrap items-center gap-2">
              <p
                id="course-niche-error"
                role="alert"
                className="text-sm text-destructive"
              >
                Não foi possível carregar os setores.
              </p>
              <Button
                variant="outline"
                size="sm"
                disabled={niches.isFetching}
                onClick={() => void niches.refetch()}
              >
                Tentar novamente
              </Button>
            </div>
          )}
        </div>
        <div className="grid gap-2">
          <Label asChild>
            <span id="course-audience-label">Nível de público</span>
          </Label>
          <RadioGroup
            aria-labelledby="course-audience-label"
            value={profile.audienceLevel ?? ""}
            onValueChange={(value) => {
              const option = audienceOptions.find(([level]) => level === value)
              if (option) onChange({ ...profile, audienceLevel: option[0] })
            }}
          >
            {audienceOptions.map(([level, description]) => (
              <Label
                key={level}
                htmlFor={level}
                className="cursor-pointer items-start gap-3 rounded-md border p-4 has-[[data-state=checked]]:border-info"
              >
                <RadioGroupItem
                  id={level}
                  value={level}
                  aria-labelledby={`${level}-label`}
                  aria-describedby={`${level}-description`}
                />
                <span className="grid gap-1">
                  <span id={`${level}-label`}>{AUDIENCE_LABELS[level]}</span>
                  <span
                    id={`${level}-description`}
                    className="text-sm font-normal text-muted-foreground"
                  >
                    {description}
                  </span>
                </span>
              </Label>
            ))}
          </RadioGroup>
        </div>
      </div>
      <div className="mt-auto flex flex-wrap items-center justify-between gap-4 border-t bg-muted/30 p-6">
        <Button
          variant="outline"
          className="min-h-12 px-[22px]"
          onClick={onBack}
        >
          Voltar
        </Button>
        <Button
          className="min-h-12 rounded-sm bg-foreground px-7 text-background hover:bg-foreground/90 disabled:bg-muted disabled:text-foreground-tertiary has-[>svg]:px-7"
          disabled={
            nichesUnavailable || !selectedNiche || !profile.audienceLevel
          }
          onClick={() => {
            setCheckedTitle(true)
            if (!titleError(profile.title)) onContinue()
          }}
        >
          Continuar <ArrowRight aria-hidden="true" />
        </Button>
      </div>
    </>
  )
}
