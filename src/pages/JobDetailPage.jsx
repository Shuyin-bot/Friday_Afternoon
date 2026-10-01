import { useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import {
  ArrowBackRounded,
  AutoAwesomeRounded,
  CheckCircleRounded,
  CommentRounded,
  DeleteOutlineRounded,
  EmailRounded,
  EditRounded,
} from "@mui/icons-material";
import { jobService } from "../services/jobService";
import { HumanReviewCard } from "../components/HumanReviewCard";

export function JobDetailPage({ job, onBack, onNotice }) {
  const [detail, setDetail] = useState(job);
  const [humanRequest, setHumanRequest] = useState(null);
  const [humanAnswer, setHumanAnswer] = useState("");
  const [loading, setLoading] = useState(Boolean(job.rawId));
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState(false);
  const [rejectOpen, setRejectOpen] = useState(false);
  const [commentOpen, setCommentOpen] = useState(false);
  const [reviewComment, setReviewComment] = useState("");
  const [draftSubject, setDraftSubject] = useState(
    job.meta_data?.draft?.subject || "",
  );
  const [draftBody, setDraftBody] = useState(job.meta_data?.draft?.body || "");

  const draft = detail.meta_data?.draft;

  useEffect(() => {
    async function loadDetails() {
      if (!job.rawId) return;
      try {
        const [jobData, requests] = await Promise.all([
          jobService.getJob(job.rawId),
          jobService.getHumanRequests(),
        ]);
        setDetail(jobData);
        setDraftSubject(jobData.meta_data?.draft?.subject || "");
        setDraftBody(jobData.meta_data?.draft?.body || "");
        setHumanRequest(
          requests.find((request) => request.queued_job_id === job.rawId) ||
            null,
        );
      } catch {
        onNotice("Could not load the full job details.");
      } finally {
        setLoading(false);
      }
    }
    loadDetails();
  }, [job.rawId, onNotice]);

  async function approveDraft() {
    if (!job.rawId) return onNotice("Draft approved in the preview.");
    setSaving(true);
    try {
      setDetail(await jobService.approveDraft(job.rawId));
      onNotice("Draft approved and marked as completed.");
    } catch {
      onNotice("Could not approve this draft.");
    } finally {
      setSaving(false);
    }
  }

  async function saveDraftEdits() {
    if (!job.rawId) {
      setDetail((current) => ({
        ...current,
        meta_data: {
          ...current.meta_data,
          draft: { subject: draftSubject, body: draftBody },
        },
      }));
      setEditing(false);
      return onNotice("Draft edits saved in the preview.");
    }
    setSaving(true);
    try {
      setDetail(
        await jobService.updateDraft(job.rawId, {
          subject: draftSubject,
          body: draftBody,
        }),
      );
      setEditing(false);
      onNotice("Draft edits saved.");
    } catch {
      onNotice("Could not save draft edits.");
    } finally {
      setSaving(false);
    }
  }

  async function rejectDraft() {
    if (!job.rawId) {
      setDetail((current) => ({
        ...current,
        status: "COMPLETED",
        meta_data: {
          ...current.meta_data,
          draft: undefined,
          review_action: "REJECTED",
        },
      }));
      setRejectOpen(false);
      return onNotice("Draft rejected and marked as complete in the preview.");
    }
    setSaving(true);
    try {
      setDetail(await jobService.rejectDraft(job.rawId));
      setRejectOpen(false);
      onNotice("Draft rejected and marked as complete.");
    } catch {
      onNotice("Could not reject this draft.");
    } finally {
      setSaving(false);
    }
  }

  async function sendReviewComment() {
    if (!reviewComment.trim()) return;
    if (!job.rawId) {
      setCommentOpen(false);
      setReviewComment("");
      return onNotice("Revision feedback saved in the preview.");
    }
    setSaving(true);
    try {
      setDetail(
        await jobService.sendDraftBackForRevision(
          job.rawId,
          reviewComment.trim(),
        ),
      );
      setCommentOpen(false);
      setReviewComment("");
      onNotice("Feedback saved. The quotation is ready for the workflow to resume.");
    } catch {
      onNotice("Could not save the review feedback.");
    } finally {
      setSaving(false);
    }
  }

  async function answerRequest() {
    if (!humanRequest || !humanAnswer.trim()) return;
    setSaving(true);
    try {
      setHumanRequest(
        await jobService.answerHumanRequest(humanRequest.id, humanAnswer),
      );
      if (job.rawId) {
        setDetail(await jobService.getJob(job.rawId));
      }
      setHumanAnswer("");
      onNotice("Human answer saved successfully.");
    } catch {
      onNotice("Could not save the human answer.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Box>
      <Button
        startIcon={<ArrowBackRounded />}
        onClick={onBack}
        sx={{ mb: 3, color: "text.secondary" }}
      >
        Back
      </Button>
      <Stack
        direction={{ xs: "column", md: "row" }}
        justifyContent="space-between"
        spacing={2}
        mb={4}
      >
        <Box>
          <Typography
            variant="overline"
            color="primary"
            fontWeight={800}
            letterSpacing=".12em"
          >
            Quotation detail
          </Typography>
          <Typography
            variant="h3"
            sx={{ fontSize: { xs: 30, md: 40 }, mt: 0.5 }}
          >
            {detail.subject || detail.title || "Quotation request"}
          </Typography>
          <Typography color="text.secondary" mt={1}>
            {detail.from_email || detail.sender}{" "}
            {detail.status && `• ${detail.status}`}
          </Typography>
        </Box>
        <Chip
          label={detail.status || "Review"}
          color={
            detail.status?.toLowerCase().includes("wait")
              ? "secondary"
              : "primary"
          }
          sx={{ fontWeight: 800, alignSelf: "flex-start" }}
        />
      </Stack>
      {loading ? (
        <Box sx={{ display: "grid", placeItems: "center", minHeight: 300 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Stack spacing={2.5}>
          {humanRequest && (
            <HumanReviewCard
              request={humanRequest}
              answer={humanAnswer}
              onAnswerChange={setHumanAnswer}
              onSubmit={answerRequest}
              saving={saving}
            />
          )}
          <Stack
            direction={{ xs: "column", lg: "row" }}
            spacing={2.5}
            alignItems="stretch"
          >
            <EmailCard body={detail.email_body} />
            <DraftCard
              draft={draft}
              editing={editing}
              subject={draftSubject}
              body={draftBody}
              saving={saving}
              onSubjectChange={setDraftSubject}
              onBodyChange={setDraftBody}
              onApprove={approveDraft}
              onEdit={() => setEditing(true)}
              onSave={saveDraftEdits}
              onReject={() => setRejectOpen(true)}
              onComment={() => setCommentOpen(true)}
            />
          </Stack>
          <Card sx={{ p: { xs: 2, md: 3 } }}>
            <Typography variant="h5" mb={2}>
              Processing metadata
            </Typography>
            <Typography
              component="pre"
              sx={{
                whiteSpace: "pre-wrap",
                overflow: "auto",
                bgcolor: "#f5f7fb",
                borderRadius: 2,
                p: 2,
                font: "12px/1.6 monospace",
                maxHeight: 230,
              }}
            >
              {JSON.stringify(detail.meta_data || {}, null, 2)}
            </Typography>
          </Card>
        </Stack>
      )}
      <Dialog
        open={rejectOpen}
        onClose={() => setRejectOpen(false)}
        fullWidth
        maxWidth="sm"
      >
        <DialogTitle>Reject and delete this draft?</DialogTitle>
        <DialogContent>
          <Typography color="text.secondary">
            This quotation will be closed, its draft removed, and the job marked
            as complete.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRejectOpen(false)}>Cancel</Button>
          <Button
            onClick={rejectDraft}
            color="error"
            variant="contained"
            disabled={saving}
          >
            Reject & delete
          </Button>
        </DialogActions>
      </Dialog>
      <Dialog
        open={commentOpen}
        onClose={() => setCommentOpen(false)}
        fullWidth
        maxWidth="sm"
      >
        <DialogTitle>Send draft back for revision</DialogTitle>
        <DialogContent>
          <Typography color="text.secondary" mb={2}>
            Tell the agent what the customer meant or how the quotation should
            change. For example: “Shipping carton means the 12-inch pizza box,
            SKU PB-12.”
          </Typography>
          <TextField
            autoFocus
            fullWidth
            multiline
            minRows={5}
            label="Review feedback"
            value={reviewComment}
            onChange={(event) => setReviewComment(event.target.value)}
            placeholder="Explain the correction..."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCommentOpen(false)}>Cancel</Button>
          <Button
            onClick={sendReviewComment}
            color="primary"
            variant="contained"
            disabled={!reviewComment.trim() || saving}
          >
            Send feedback
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

function EmailCard({ body }) {
  return (
    <Card sx={{ p: { xs: 2, md: 3 }, flex: 1 }}>
      <Stack
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        mb={2}
      >
        <Typography variant="h5">Original email</Typography>
        <Chip icon={<EmailRounded />} label="Inbound" size="small" />
      </Stack>
      <Divider sx={{ mb: 2 }} />
      <Typography component="pre" sx={preformattedText}>
        {body || "No email body available."}
      </Typography>
    </Card>
  );
}

function DraftCard({
  draft,
  editing,
  subject,
  body,
  saving,
  onSubjectChange,
  onBodyChange,
  onApprove,
  onEdit,
  onSave,
  onReject,
  onComment,
}) {
  return (
    <Card sx={{ p: { xs: 2, md: 3 }, flex: 1, bgcolor: "#f8f9ff" }}>
      <Stack
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        mb={2}
      >
        <Typography variant="h5">Drafted response</Typography>
        <Chip
          icon={<AutoAwesomeRounded />}
          label={draft ? "AI draft" : "Not drafted"}
          size="small"
          color={draft ? "primary" : "default"}
        />
      </Stack>
      <Divider sx={{ mb: 2 }} />
      {draft ? (
        <Box>
          {editing ? (
            <Stack spacing={2}>
              <TextField
                label="Subject"
                value={subject}
                onChange={(event) => onSubjectChange(event.target.value)}
                fullWidth
              />
              <TextField
                label="Message"
                value={body}
                onChange={(event) => onBodyChange(event.target.value)}
                multiline
                minRows={10}
                fullWidth
              />
            </Stack>
          ) : (
            <>
              <Typography fontWeight={800} mb={1}>
                {draft.subject}
              </Typography>
              <Typography component="pre" sx={preformattedText}>
                {draft.body}
              </Typography>
            </>
          )}
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap mt={2}>
            <Button
              size="small"
              variant="contained"
              color="success"
              startIcon={<CheckCircleRounded />}
              onClick={onApprove}
              disabled={saving}
            >
              Approve
            </Button>
            {editing ? (
              <Button
                size="small"
                variant="outlined"
                onClick={onSave}
                disabled={saving}
              >
                Save edits
              </Button>
            ) : (
              <Button
                size="small"
                variant="outlined"
                startIcon={<EditRounded />}
                onClick={onEdit}
                disabled={saving}
              >
                Edit draft
              </Button>
            )}
            <Button
              size="small"
              color="error"
              startIcon={<DeleteOutlineRounded />}
              onClick={onReject}
              disabled={saving}
            >
              Reject & delete
            </Button>
            <Button
              size="small"
              color="warning"
              startIcon={<CommentRounded />}
              onClick={onComment}
              disabled={saving}
            >
              Reject & comment
            </Button>
          </Stack>
        </Box>
      ) : (
        <Alert severity="info">
          A quotation draft will appear here once the workflow finishes.
        </Alert>
      )}
    </Card>
  );
}

const preformattedText = {
  whiteSpace: "pre-wrap",
  overflowWrap: "anywhere",
  font: "13px/1.7 Inter, sans-serif",
  color: "text.secondary",
  m: 0,
};
