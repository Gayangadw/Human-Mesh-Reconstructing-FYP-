using UnityEngine;
using System.Collections.Generic;
using System.Collections;

public class CameraController : MonoBehaviour
{
    public Transform[] targets;
    public float smoothSpeed = 0.125f;
    public Vector3 offset;
    
    void LateUpdate()
    {
        if (targets == null || targets.Length == 0)
        {
            return;
        }
        
        Transform activeTarget = FindActiveTarget();
        if (activeTarget == null)
            return;
            
        Vector3 desiredPosition = activeTarget.position + offset;
        desiredPosition.y = transform.position.y;
        Vector3 smoothPosition = Vector3.Lerp(transform.position, desiredPosition, smoothSpeed);
        transform.position = smoothPosition;
    }
    
    Transform FindActiveTarget()
    {
        foreach(Transform target in targets)
        {
            if(target.gameObject.activeInHierarchy)
                return target;
        }
        return null; // Return null if no active target is found
    }
}