using UnityEngine;

public class FightingCharacter : MonoBehaviour
{
    [Header("Player Movement")]
    public float movementSpeed = 1f;
    public float rotationSpeed = 10f;

    private CharacterController characterController;
    private Animator animator;

    [Header("Player Fight")]
    public float attackCooldown = 0.5f;
    public int attackDamage = 5;
    public string[] attackAnimation = { "Attack1Animation", "Attack2Animation", "Attack3Animation", "Attack4Animation" };

    private float lastAttackTime;

    void Start()
    {
        characterController = GetComponent<CharacterController>();
        animator = GetComponent<Animator>();
    }

    void Update()
    {
        PerformMovement();

        if (Input.GetKeyDown(KeyCode.Alpha1)) performAttack(0);
        else if (Input.GetKeyDown(KeyCode.Alpha2)) performAttack(1);
        else if (Input.GetKeyDown(KeyCode.Alpha3)) performAttack(2);
        else if (Input.GetKeyDown(KeyCode.Alpha4)) performAttack(3);
    }

    void PerformMovement()
    {
        float horizontalInput = Input.GetAxis("Horizontal");
        float verticalInput = Input.GetAxis("Vertical");

        Vector3 movement = new Vector3(horizontalInput, 0f, verticalInput);

        if (movement != Vector3.zero)
        {
            Quaternion targetRotation = Quaternion.LookRotation(movement);
            transform.rotation = Quaternion.Slerp(transform.rotation, targetRotation, rotationSpeed * Time.deltaTime);
        }

        characterController.Move(movement * movementSpeed * Time.deltaTime);
    }

    void performAttack(int attackIndex)
    {
        if (Time.time - lastAttackTime > attackCooldown)
        {
            animator.Play(attackAnimation[attackIndex]);
            Debug.Log($"Performed attack {attackIndex + 1}, dealing {attackDamage} damage");
            lastAttackTime = Time.time;
        }
        else
        {
            float remainingTime = attackCooldown - (Time.time - lastAttackTime);
            Debug.Log($"Cannot perform attack yet. Cooldown time remaining: {remainingTime:F2} seconds.");
        }
    }
}
