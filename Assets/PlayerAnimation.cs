using UnityEngine;

public class PlayerAnimation : MonoBehaviour
{
    public Animator animator;
    public PlayerController player;

    private void Awake()
    {
        if (animator == null)
            animator = GetComponentInChildren<Animator>();

        if (player == null)
            player = GetComponent<PlayerController>();
    }

    private void OnEnable()
    {
        if (player == null)
            return;

        player.OnPathStarted += HandlePathStarted;
        player.OnPathCompleted += HandlePathCompleted;
    }

    private void OnDisable()
    {
        if (player == null)
            return;

        player.OnPathStarted -= HandlePathStarted;
        player.OnPathCompleted -= HandlePathCompleted;
    }

    private void Start()
    {
        SetWalking(false);
    }

    private void HandlePathStarted()
    {
        SetWalking(true);
    }

    private void HandlePathCompleted()
    {
        SetWalking(false);
    }

    private void SetWalking(bool value)
    {
        if (animator != null)
            animator.SetBool("walking", value);
    }
}
